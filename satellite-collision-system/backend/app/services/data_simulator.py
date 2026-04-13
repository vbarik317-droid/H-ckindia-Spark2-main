"""
Data simulator for when API rate limits are reached
Generates realistic satellite data for testing
"""
import math
import random
from datetime import datetime, timedelta
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class DataSimulator:
    """
    Simulate satellite data when APIs are rate-limited
    """
    
    def __init__(self):
        random.seed(42)  # For reproducibility
        
    def generate_tle_line(self, norad_id: str, epoch: datetime) -> tuple:
        """
        Generate simulated TLE lines
        """
        # Generate random orbital elements
        inclination = random.uniform(0, 98)
        raan = random.uniform(0, 360)
        eccentricity = random.uniform(0, 0.1)
        arg_perigee = random.uniform(0, 360)
        mean_anomaly = random.uniform(0, 360)
        mean_motion = random.uniform(12, 16)  # revs per day for LEO
        
        # Format epoch
        year = epoch.year % 100
        day_of_year = epoch.timetuple().tm_yday + epoch.hour/24.0 + epoch.minute/1440.0
        
        # Create TLE lines
        line1 = (f"1 {norad_id}U {year:02d}{day_of_year:012.8f} "
                f"{random.random():.8f} {random.random():.8f} 0000000 "
                f"00000{random.randint(0,9)}")
        
        line2 = (f"2 {norad_id} {inclination:8.4f} {raan:8.4f} "
                f"{eccentricity*10000:07.0f} {arg_perigee:8.4f} "
                f"{mean_anomaly:8.4f} {mean_motion:11.8f}")
        
        return line1, line2
    
    def generate_satellite(self, norad_id: str = None) -> Dict:
        """
        Generate a single simulated satellite
        """
        if norad_id is None:
            norad_id = f"{random.randint(10000, 99999)}"
        
        # Satellite names
        prefixes = ['ISS', 'HUBBLE', 'GPS', 'GEO', 'LEO', 'DEBRIS', 'COSMOS']
        suffixes = ['A', 'B', 'C', '1', '2', '3']
        
        name = f"{random.choice(prefixes)}-{random.choice(suffixes)}-{norad_id[-3:]}"
        
        # Object types
        obj_types = ['PAYLOAD', 'DEBRIS', 'ROCKET BODY']
        obj_type = random.choices(obj_types, weights=[0.6, 0.3, 0.1])[0]
        
        # Countries
        countries = ['USA', 'RUSSIA', 'CHINA', 'ESA', 'JAPAN', 'INDIA', 'OTHER']
        country = random.choice(countries)
        
        # Generate epoch
        epoch = datetime.now() - timedelta(days=random.randint(0, 30))
        
        # Generate TLE
        tle_line1, tle_line2 = self.generate_tle_line(norad_id, epoch)
        
        # Parse orbital elements from TLE (simulated)
        inclination = float(tle_line2[8:16].strip())
        raan = float(tle_line2[17:25].strip())
        eccentricity = float("0." + tle_line2[26:33].strip())
        arg_perigee = float(tle_line2[34:42].strip())
        mean_anomaly = float(tle_line2[43:51].strip())
        mean_motion = float(tle_line2[52:63].strip())
        
        # Generate random position based on orbital elements (simplified)
        # This is just for simulation - real positions would come from propagation
        a = 7000  # Approximate semi-major axis for LEO
        x = random.uniform(-a, a)
        y = random.uniform(-a, a)
        z = random.uniform(-a, a)
        
        # Normalize to roughly correct altitude
        r = math.sqrt(x**2 + y**2 + z**2)
        scale = 7000 / r
        x *= scale
        y *= scale
        z *= scale
        
        # Generate velocity (roughly circular orbit)
        v_mag = math.sqrt(398600 / 7000)  # ~7.5 km/s
        
        # Make velocity perpendicular to position (simplified)
        # Cross product approximation
        if abs(x) > abs(y):
            vx = 0
            vy = v_mag * (1 if x > 0 else -1)
            vz = 0
        else:
            vx = v_mag * (1 if y > 0 else -1)
            vy = 0
            vz = 0
        
        altitude = math.sqrt(x**2 + y**2 + z**2) - 6371
        
        return {
            'norad_id': norad_id,
            'name': name,
            'country': country,
            'object_type': obj_type,
            'tle_line1': tle_line1,
            'tle_line2': tle_line2,
            'epoch': epoch,
            'inclination': inclination,
            'raan': raan,
            'eccentricity': eccentricity,
            'arg_perigee': arg_perigee,
            'mean_anomaly': mean_anomaly,
            'mean_motion': mean_motion,
            'pos_x': x,
            'pos_y': y,
            'pos_z': z,
            'vel_x': vx,
            'vel_y': vy,
            'vel_z': vz,
            'altitude': altitude,
            'is_active': True
        }
    
    def generate_satellites(self, count: int = 100) -> List[Dict]:
        """
        Generate multiple simulated satellites
        """
        satellites = []
        for i in range(count):
            norad_id = f"{40000 + i}"
            satellite = self.generate_satellite(norad_id)
            satellites.append(satellite)
        
        logger.info(f"Generated {count} simulated satellites")
        return satellites
    
    def generate_position_history(self, satellite: Dict, 
                                 hours: int = 48,
                                 step_minutes: int = 5) -> List[Dict]:
        """
        Generate historical position data for a satellite
        """
        positions = []
        total_steps = hours * 60 // step_minutes
        
        # Orbital period (simplified)
        period = 90  # minutes for LEO
        
        for step in range(total_steps):
            t = step * step_minutes / period * 2 * math.pi
            
            # Simulate circular orbit with some variation
            altitude = 400 + 50 * math.sin(t / 10)
            r = 6371 + altitude
            
            # Position in orbital plane (simplified)
            x = r * math.cos(t)
            y = r * math.sin(t) * math.cos(satellite['inclination'] * math.pi/180)
            z = r * math.sin(t) * math.sin(satellite['inclination'] * math.pi/180)
            
            # Velocity (simplified)
            v_mag = math.sqrt(398600 / r)
            vx = -v_mag * math.sin(t)
            vy = v_mag * math.cos(t) * math.cos(satellite['inclination'] * math.pi/180)
            vz = v_mag * math.cos(t) * math.sin(satellite['inclination'] * math.pi/180)
            
            timestamp = datetime.now() - timedelta(hours=hours - step*step_minutes/60)
            
            positions.append({
                'norad_id': satellite['norad_id'],
                'satellite_id': 0,  # Will be set when inserting
                'timestamp': timestamp,
                'pos_x': x,
                'pos_y': y,
                'pos_z': z,
                'vel_x': vx,
                'vel_y': vy,
                'vel_z': vz,
                'altitude': altitude,
                'inclination': satellite['inclination'],
                'eccentricity': satellite['eccentricity'],
                'mean_motion': satellite['mean_motion'],
                'data_source': 'simulated'
            })
        
        return positions