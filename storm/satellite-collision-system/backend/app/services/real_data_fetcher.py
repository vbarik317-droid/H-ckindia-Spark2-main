"""
Real satellite data fetcher from multiple sources
"""
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
from spacetrack import SpaceTrackClient

logger = logging.getLogger(__name__)

class RealDataFetcher:
    """
    Fetches real satellite data from multiple authoritative sources
    """
    
    def __init__(self, db_session):
        self.db = db_session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SatelliteCollisionSystem/1.0'
        })
        
        # Initialize Space-Track client if credentials available
        from app.config import config
        self.config = config
        self.st = None
        if config.SPACE_TRACK_USER and config.SPACE_TRACK_PASS:
            try:
                self.st = SpaceTrackClient(
                    identity=config.SPACE_TRACK_USER,
                    password=config.SPACE_TRACK_PASS
                )
                logger.info("Space-Track client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Space-Track client: {e}")
    
    def fetch_from_spacetrack(self, limit: int = 100) -> List[Dict]:
        """
        Fetch real TLE data from Space-Track.org [citation:2]
        This is the most authoritative source for U.S. Space Surveillance Network data
        """
        satellites = []
        
        if not self.st:
            logger.warning("Space-Track client not initialized")
            return satellites
        
        try:
            logger.info("Fetching real TLE data from Space-Track.org...")
            
            # Get latest TLEs for active satellites
            # Space-Track recommends limiting to 1 request per hour for TLEs [citation:2]
            data = self.st.tle_latest(
                epoch=">now-30",
                decay_date=None,
                orderby="norad_cat_id",
                format="tle",
                limit=limit
            )
            
            if data:
                # Parse the TLE data
                lines = data.strip().split('\n')
                for i in range(0, len(lines), 3):
                    if i + 2 < len(lines):
                        name = lines[i].strip()
                        line1 = lines[i+1].strip()
                        line2 = lines[i+2].strip()
                        
                        # Extract NORAD ID from TLE
                        norad_id = line1[2:7].strip()
                        
                        # Parse epoch from TLE
                        epoch_year = int(line1[18:20])
                        epoch_day = float(line1[20:32])
                        
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
                            'object_type': self._determine_object_type(norad_id),
                            'tle_line1': line1,
                            'tle_line2': line2,
                            'epoch': epoch,
                            'inclination': inclination,
                            'raan': raan,
                            'eccentricity': eccentricity,
                            'arg_perigee': arg_perigee,
                            'mean_anomaly': mean_anomaly,
                            'mean_motion': mean_motion,
                            'source': 'spacetrack',
                            'is_active': True
                        })
                
                logger.info(f"Fetched {len(satellites)} real satellites from Space-Track")
                
        except Exception as e:
            logger.error(f"Error fetching from Space-Track: {e}")
        
        return satellites
    
    def fetch_from_celestrak(self, group: str = 'active') -> List[Dict]:
        """
        Fetch real TLE data from CelesTrak [citation:1][citation:9]
        CelesTrak is maintained by T.S. Kelso and provides authoritative TLE data
        """
        satellites = []
        
        try:
            url = f"{self.config.CELESTRAK_URL}?GROUP={group}&FORMAT=tle"
            logger.info(f"Fetching real data from CelesTrak: {group}")
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                
                for i in range(0, len(lines), 3):
                    if i + 2 < len(lines):
                        try:
                            name = lines[i].strip()
                            line1 = lines[i+1].strip()
                            line2 = lines[i+2].strip()
                            
                            norad_id = line1[2:7].strip()
                            
                            # Parse epoch
                            epoch_year = int(line1[18:20])
                            epoch_day = float(line1[20:32])
                            
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
                                'object_type': self._determine_object_type(norad_id),
                                'tle_line1': line1,
                                'tle_line2': line2,
                                'epoch': epoch,
                                'inclination': inclination,
                                'raan': raan,
                                'eccentricity': eccentricity,
                                'arg_perigee': arg_perigee,
                                'mean_anomaly': mean_anomaly,
                                'mean_motion': mean_motion,
                                'source': 'celestrak',
                                'is_active': True
                            })
                            
                        except Exception as e:
                            logger.error(f"Error parsing TLE: {e}")
                            continue
                
                logger.info(f"Fetched {len(satellites)} real satellites from CelesTrak")
            else:
                logger.error(f"CelesTrak returned {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error fetching from CelesTrak: {e}")
        
        return satellites
    
    def fetch_from_n2yo(self, satellite_id: str) -> Optional[Dict]:
        """
        Fetch real-time satellite data from N2YO.com [citation:3][citation:7]
        Good for getting current positions of specific satellites
        """
        if not self.config.N2YO_API_KEY:
            logger.warning("N2YO API key not configured")
            return None
        
        try:
            # Get TLE data for specific satellite
            url = f"https://api.n2yo.com/rest/v1/satellite/tle/{satellite_id}&apiKey={self.config.N2YO_API_KEY}"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse TLE from response
                tle_lines = data['tle'].split('\r\n')
                
                if len(tle_lines) >= 2:
                    line1 = tle_lines[0]
                    line2 = tle_lines[1]
                    
                    return {
                        'norad_id': str(data['info']['satid']),
                        'name': data['info']['satname'],
                        'tle_line1': line1,
                        'tle_line2': line2,
                        'epoch': datetime.now(),
                        'source': 'n2yo',
                        'is_active': True
                    }
            
        except Exception as e:
            logger.error(f"Error fetching from N2YO: {e}")
        
        return None
    
    def get_satellite_positions(self, satellite_id: str, observer_lat: float = 0, 
                                observer_lon: float = 0, seconds: int = 300) -> Optional[List[Dict]]:
        """
        Get real-time positions from N2YO [citation:7]
        """
        if not self.config.N2YO_API_KEY:
            return None
        
        try:
            url = (f"https://api.n2yo.com/rest/v1/satellite/positions/"
                   f"{satellite_id}/{observer_lat}/{observer_lon}/0/{seconds}/"
                   f"&apiKey={self.config.N2YO_API_KEY}")
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                positions = []
                
                for pos in data['positions']:
                    positions.append({
                        'timestamp': datetime.fromtimestamp(pos['timestamp']),
                        'satlatitude': pos['satlatitude'],
                        'satlongitude': pos['satlongitude'],
                        'sataltitude': pos['sataltitude'],
                        'azimuth': pos['azimuth'],
                        'elevation': pos['elevation'],
                        'ra': pos['ra'],
                        'dec': pos['dec']
                    })
                
                return positions
            
        except Exception as e:
            logger.error(f"Error getting positions from N2YO: {e}")
        
        return None
    
    def _determine_object_type(self, norad_id: str) -> str:
        """Determine object type based on NORAD ID range"""
        norad_num = int(norad_id)
        
        if norad_num < 20000:
            return 'PAYLOAD'
        elif 20000 <= norad_num < 30000:
            return 'DEBRIS'
        elif 30000 <= norad_num < 40000:
            return 'ROCKET BODY'
        else:
            return 'UNKNOWN'
    
    def fetch_all_real_data(self) -> Dict[str, int]:
        """
        Fetch real data from all available sources
        """
        results = {
            'spacetrack': 0,
            'celestrak': 0,
            'n2yo': 0,
            'total': 0
        }
        
        from app.database.models import Satellite
        
        # 1. Fetch from Space-Track (most authoritative) [citation:2]
        if self.st:
            spacetrack_sats = self.fetch_from_spacetrack(limit=200)
            for sat_data in spacetrack_sats:
                self._store_satellite(sat_data)
            results['spacetrack'] = len(spacetrack_sats)
            results['total'] += len(spacetrack_sats)
            
            # Respect rate limits - wait 1 second [citation:2]
            time.sleep(1)
        
        # 2. Fetch from CelesTrak [citation:1]
        celestrak_sats = self.fetch_from_celestrak('active')
        for sat_data in celestrak_sats:
            self._store_satellite(sat_data)
        results['celestrak'] = len(celestrak_sats)
        results['total'] += len(celestrak_sats)
        
        # 3. Fetch specific high-interest satellites from N2YO
        high_interest_sats = ['25544']  # ISS
        for sat_id in high_interest_sats:
            sat_data = self.fetch_from_n2yo(sat_id)
            if sat_data:
                self._store_satellite(sat_data)
                results['n2yo'] += 1
                results['total'] += 1
                time.sleep(2)  # N2YO free tier rate limit
        
        self.db.commit()
        logger.info(f"Real data fetch complete: {results}")
        
        return results
    
    def _store_satellite(self, sat_data: Dict):
        """Store satellite in database"""
        from app.database.models import Satellite, TLEHistory
        
        # Check if exists
        satellite = self.db.query(Satellite).filter_by(
            norad_id=sat_data['norad_id']
        ).first()
        
        if satellite:
            # Update existing
            for key, value in sat_data.items():
                if hasattr(satellite, key):
                    setattr(satellite, key, value)
            satellite.updated_at = datetime.now()
        else:
            # Create new
            satellite = Satellite(**sat_data)
            self.db.add(satellite)
        
        # Store TLE history
        tle_record = TLEHistory(
            norad_id=sat_data['norad_id'],
            tle_line1=sat_data.get('tle_line1', ''),
            tle_line2=sat_data.get('tle_line2', ''),
            epoch=sat_data.get('epoch', datetime.now())
        )
        self.db.add(tle_record)