"""
TLE Data Fetcher - Retrieves satellite data from multiple sources
"""
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time

from app.config import config
from app.database.models import Satellite, TLEHistory

logger = logging.getLogger(__name__)

class TLEFetcher:
    """Fetch TLE data from various sources with fallback"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SatelliteCollisionSystem/1.0'
        })
        self.config = config
        
    def fetch_from_celestrak(self, group='active') -> List[Dict]:
        """
        Fetch TLE data from CelesTrak
        Args:
            group: Satellite group (active, weather, etc.)
        Returns:
            List of parsed satellite data
        """
        try:
            url = f"{self.config.CELESTRAK_URL}?GROUP={group}&FORMAT=tle"
            logger.info(f"Fetching from CelesTrak: {url}")
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                satellites = self._parse_tle_response(response.text)
                # Add source to each satellite
                for sat in satellites:
                    sat['source'] = 'celestrak'
                return satellites
            else:
                logger.error(f"CelesTrak returned {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching from CelesTrak: {e}")
            return []
    
    def fetch_from_space_track(self, limit=100) -> List[Dict]:
        """
        Fetch from Space-Track (requires authentication)
        """
        if not (self.config.SPACE_TRACK_USER and self.config.SPACE_TRACK_PASS):
            logger.warning("Space-Track credentials not configured")
            return []
            
        try:
            # Login to Space-Track
            login_url = "https://www.space-track.org/ajaxauth/login"
            credentials = {
                'identity': self.config.SPACE_TRACK_USER,
                'password': self.config.SPACE_TRACK_PASS
            }
            
            login_resp = self.session.post(login_url, data=credentials)
            if login_resp.status_code == 200:
                # Query for recent TLEs
                query = (f"https://www.space-track.org/basicspacedata/query/"
                        f"class/tle/orderby/epoch desc/limit/{limit}/format/tle")
                response = self.session.get(query)
                
                if response.status_code == 200:
                    satellites = self._parse_tle_response(response.text)
                    # Add source to each satellite
                    for sat in satellites:
                        sat['source'] = 'spacetrack'
                    return satellites
                else:
                    logger.error(f"Space-Track query returned {response.status_code}")
            else:
                logger.error(f"Space-Track login failed: {login_resp.status_code}")
            
            return []
            
        except Exception as e:
            logger.error(f"Space-Track fetch error: {e}")
            return []
    
    def fetch_from_n2yo(self, satellite_id: str) -> Optional[Dict]:
        """
        Fetch from N2YO API (rate limited)
        """
        if not self.config.N2YO_API_KEY:
            return None
            
        try:
            url = (f"https://api.n2yo.com/rest/v1/satellite/tle/"
                   f"{satellite_id}&apiKey={self.config.N2YO_API_KEY}")
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                tle_lines = data['tle'].split('\r\n')
                sat_data = {
                    'norad_id': str(data['info']['satid']),
                    'name': data['info']['satname'],
                    'tle_line1': tle_lines[0],
                    'tle_line2': tle_lines[1],
                    'epoch': datetime.now(),
                    'source': 'n2yo'
                }
                return sat_data
            else:
                logger.error(f"N2YO returned {response.status_code}")
                return None
            
        except Exception as e:
            logger.error(f"N2YO fetch error: {e}")
            return None
    
    def _parse_tle_response(self, tle_text: str) -> List[Dict]:
        """
        Parse TLE text into structured data
        """
        satellites = []
        lines = tle_text.strip().split('\n')
        
        for i in range(0, len(lines), 3):
            if i + 2 < len(lines):
                try:
                    name = lines[i].strip()
                    line1 = lines[i + 1].strip()
                    line2 = lines[i + 2].strip()
                    
                    # Extract basic TLE data
                    norad_id = line1[2:7].strip()
                    
                    # Parse epoch
                    epoch_year = int(line1[18:20])
                    epoch_day = float(line1[20:32])
                    
                    # Calculate epoch datetime
                    if epoch_year < 57:
                        year = 2000 + epoch_year
                    else:
                        year = 1900 + epoch_year
                    
                    epoch = datetime(year, 1, 1) + timedelta(days=epoch_day - 1)
                    
                    # Parse orbital elements
                    inclination = float(line2[8:16].strip())
                    raan = float(line2[17:25].strip())
                    eccentricity = float("0." + line2[26:33].strip())
                    arg_perigee = float(line2[34:42].strip())
                    mean_anomaly = float(line2[43:51].strip())
                    mean_motion = float(line2[52:63].strip())
                    
                    satellites.append({
                        'norad_id': norad_id,
                        'name': name,
                        'tle_line1': line1,
                        'tle_line2': line2,
                        'epoch': epoch,
                        'inclination': inclination,
                        'raan': raan,
                        'eccentricity': eccentricity,
                        'arg_perigee': arg_perigee,
                        'mean_anomaly': mean_anomaly,
                        'mean_motion': mean_motion,
                        'object_type': self._determine_object_type(norad_id)
                    })
                    
                except Exception as e:
                    logger.error(f"Error parsing TLE at line {i}: {e}")
                    continue
        
        return satellites
    
    def _determine_object_type(self, norad_id: str) -> str:
        """Determine object type based on NORAD ID range"""
        try:
            norad_num = int(norad_id)
            
            if norad_num < 20000:
                return 'PAYLOAD'
            elif 20000 <= norad_num < 30000:
                return 'DEBRIS'
            elif 30000 <= norad_num < 40000:
                return 'ROCKET BODY'
            else:
                return 'UNKNOWN'
        except:
            return 'UNKNOWN'
    
    def fetch_and_store(self) -> Dict[str, int]:
        """
        Main method to fetch from all sources and store in database
        Returns a dictionary with counts from each source
        """
        logger.info("="*60)
        logger.info("FETCHING REAL SATELLITE DATA")
        logger.info("="*60)
        
        if self.config.SIMULATION_MODE:
            logger.warning("SIMULATION_MODE is true - not fetching real data")
            return {'status': 'simulation_mode', 'total': 0}
        
        results = {'status': 'success', 'sources': {}}
        total_count = 0
        
        # Try Space-Track first (most authoritative)
        if self.config.SPACE_TRACK_USER and self.config.SPACE_TRACK_PASS:
            logger.info("Fetching from Space-Track.org...")
            try:
                satellites = self.fetch_from_space_track(limit=200)
                self._store_satellites(satellites)
                results['sources']['spacetrack'] = len(satellites)
                total_count += len(satellites)
                logger.info(f"Space-Track fetched: {len(satellites)} satellites")
                
                # Respect rate limits - wait 1 second
                time.sleep(1)
            except Exception as e:
                logger.error(f"Space-Track fetch failed: {e}")
                results['sources']['spacetrack'] = 0
        
        # Then CelesTrak
        logger.info("Fetching from CelesTrak...")
        try:
            satellites = self.fetch_from_celestrak('active')
            self._store_satellites(satellites)
            results['sources']['celestrak'] = len(satellites)
            total_count += len(satellites)
            logger.info(f"CelesTrak fetched: {len(satellites)} satellites")
        except Exception as e:
            logger.error(f"CelesTrak fetch failed: {e}")
            results['sources']['celestrak'] = 0
        
        # Try N2YO for specific high-interest satellites
        if self.config.N2YO_API_KEY:
            logger.info("Fetching specific high-interest satellites from N2YO...")
            try:
                high_interest_sats = ['25544', '20580', '33591']  # ISS, Hubble, etc.
                n2yo_count = 0
                for sat_id in high_interest_sats:
                    sat_data = self.fetch_from_n2yo(sat_id)
                    if sat_data:
                        self._store_satellites([sat_data])
                        n2yo_count += 1
                        time.sleep(2)  # Respect N2YO rate limits
                results['sources']['n2yo'] = n2yo_count
                total_count += n2yo_count
                logger.info(f"N2YO fetched: {n2yo_count} satellites")
            except Exception as e:
                logger.error(f"N2YO fetch failed: {e}")
                results['sources']['n2yo'] = 0
        
        # Commit all changes
        try:
            self.db.commit()
            logger.info(f"Successfully committed {total_count} satellites to database")
        except Exception as e:
            logger.error(f"Database commit failed: {e}")
            self.db.rollback()
            results['status'] = 'partial_failure'
        
        results['total'] = total_count
        logger.info(f"Successfully fetched {total_count} satellites total")
        
        return results
    
    def _store_satellites(self, satellites_data: List[Dict]):
        """
        Store satellite data in database with improved error handling
        """
        for sat_data in satellites_data:
            try:
                # Ensure required fields exist
                if 'norad_id' not in sat_data:
                    logger.error("Satellite data missing norad_id")
                    continue
                
                # Check if satellite exists
                satellite = self.db.query(Satellite).filter_by(
                    norad_id=sat_data['norad_id']
                ).first()
                
                # Prepare data for storage with defaults
                store_data = {
                    'norad_id': sat_data.get('norad_id'),
                    'name': sat_data.get('name', 'Unknown'),
                    'object_type': sat_data.get('object_type', 'UNKNOWN'),
                    'tle_line1': sat_data.get('tle_line1', ''),
                    'tle_line2': sat_data.get('tle_line2', ''),
                    'epoch': sat_data.get('epoch', datetime.now()),
                    'inclination': sat_data.get('inclination', 0.0),
                    'raan': sat_data.get('raan', 0.0),
                    'eccentricity': sat_data.get('eccentricity', 0.0),
                    'arg_perigee': sat_data.get('arg_perigee', 0.0),
                    'mean_anomaly': sat_data.get('mean_anomaly', 0.0),
                    'mean_motion': sat_data.get('mean_motion', 0.0),
                    'source': sat_data.get('source', 'unknown'),  # Now this will work
                    'is_active': True
                }
                
                if satellite:
                    # Update existing
                    for key, value in store_data.items():
                        if hasattr(satellite, key):
                            setattr(satellite, key, value)
                    satellite.updated_at = datetime.now()
                    logger.debug(f"Updated satellite {sat_data['norad_id']}")
                else:
                    # Create new
                    satellite = Satellite(**store_data)
                    self.db.add(satellite)
                    logger.debug(f"Added new satellite {sat_data['norad_id']}")
                
                # Store TLE history
                tle_record = TLEHistory(
                    norad_id=sat_data['norad_id'],
                    tle_line1=sat_data.get('tle_line1', ''),
                    tle_line2=sat_data.get('tle_line2', ''),
                    epoch=sat_data.get('epoch', datetime.now()),
                    source=sat_data.get('source', 'unknown')
                )
                self.db.add(tle_record)
                
            except Exception as e:
                logger.error(f"Error storing satellite {sat_data.get('norad_id', 'unknown')}: {e}")
                continue