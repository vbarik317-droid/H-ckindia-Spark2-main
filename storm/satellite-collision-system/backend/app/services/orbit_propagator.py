"""
Orbit propagation using simplified SGP4 algorithm
Note: For hackathon, we use a simplified model
"""
import math
from datetime import datetime, timedelta
from typing import Tuple, List, Dict
import logging
from sgp4.api import Satrec, jday
logger = logging.getLogger(__name__)

class OrbitPropagator:
    """
    Simplified orbit propagator for satellite position calculation
    Uses Keplerian orbit approximation (simplified for hackathon)
    """
    
    def __init__(self):
        self.mu_earth = 398600.4418  # Earth's gravitational parameter (km³/s²)
        self.earth_radius = 6371.0  # Earth's radius (km)
        
    def tle_to_keplerian(self, tle_line1: str, tle_line2: str) -> Dict:
        """
        Convert TLE to Keplerian elements (simplified)
        """
        # Parse from TLE line2
        inclination = float(tle_line2[8:16].strip()) * math.pi / 180.0  # radians
        raan = float(tle_line2[17:25].strip()) * math.pi / 180.0  # radians
        eccentricity = float("0." + tle_line2[26:33].strip())
        arg_perigee = float(tle_line2[34:42].strip()) * math.pi / 180.0  # radians
        mean_anomaly = float(tle_line2[43:51].strip()) * math.pi / 180.0  # radians
        mean_motion = float(tle_line2[52:63].strip())  # revs per day
        
        # Calculate semi-major axis from mean motion
        n = mean_motion * 2 * math.pi / 86400.0  # rad/s
        semi_major_axis = (self.mu_earth / (n * n)) ** (1/3)
        
        return {
            'semi_major_axis': semi_major_axis,
            'eccentricity': eccentricity,
            'inclination': inclination,
            'raan': raan,
            'arg_perigee': arg_perigee,
            'mean_anomaly': mean_anomaly,
            'mean_motion': mean_motion
        }
    
    def kepler_to_eci(self, keplerian: Dict, time_from_epoch: float) -> Tuple[float, float, float]:
        """
        Convert Keplerian elements to ECI coordinates at given time
        Simplified 2-body propagation
        """
        # Extract elements
        a = keplerian['semi_major_axis']
        e = keplerian['eccentricity']
        i = keplerian['inclination']
        raan = keplerian['raan']
        arg_perigee = keplerian['arg_perigee']
        m0 = keplerian['mean_anomaly']
        n = math.sqrt(self.mu_earth / a**3)  # Mean motion in rad/s
        
        # Mean anomaly at time t
        m = m0 + n * time_from_epoch
        
        # Solve Kepler's equation for eccentric anomaly (E)
        # Using Newton's method (simplified)
        E = m
        for _ in range(5):  # 5 iterations usually enough
            E = E - (E - e * math.sin(E) - m) / (1 - e * math.cos(E))
        
        # True anomaly
        nu = 2 * math.atan2(
            math.sqrt(1 + e) * math.sin(E / 2),
            math.sqrt(1 - e) * math.cos(E / 2)
        )
        
        # Distance from Earth center
        r = a * (1 - e * math.cos(E))
        
        # Position in orbital plane
        x_orb = r * math.cos(nu)
        y_orb = r * math.sin(nu)
        
        # Rotate to ECI frame
        cos_raan = math.cos(raan)
        sin_raan = math.sin(raan)
        cos_i = math.cos(i)
        sin_i = math.sin(i)
        cos_w = math.cos(arg_perigee)
        sin_w = math.sin(arg_perigee)
        
        # Position vector
        x = x_orb * (cos_raan * cos_w - sin_raan * sin_w * cos_i) - y_orb * (cos_raan * sin_w + sin_raan * cos_w * cos_i)
        y = x_orb * (sin_raan * cos_w + cos_raan * sin_w * cos_i) - y_orb * (sin_raan * sin_w - cos_raan * cos_w * cos_i)
        z = x_orb * (sin_w * sin_i) + y_orb * (cos_w * sin_i)
        
        return x, y, z
    
    def calculate_position(self, tle_line1: str, tle_line2: str, 
                          target_time: datetime) -> Dict:
        """
        Calculate satellite position at given time
        """
        # Parse epoch from TLE
        epoch_year = int(tle_line1[18:20])
        epoch_day = float(tle_line1[20:32])
        
        if epoch_year < 57:
            year = 2000 + epoch_year
        else:
            year = 1900 + epoch_year
        
        epoch = datetime(year, 1, 1) + timedelta(days=epoch_day - 1)
        
        # Time from epoch in seconds
        time_from_epoch = (target_time - epoch).total_seconds()
        
        # Get Keplerian elements
        keplerian = self.tle_to_keplerian(tle_line1, tle_line2)
        
        # Calculate position
        x, y, z = self.kepler_to_eci(keplerian, time_from_epoch)
        
        # Calculate altitude
        altitude = math.sqrt(x**2 + y**2 + z**2) - self.earth_radius
        
        # Calculate velocity (simplified - difference approximation)
        dt = 1.0  # 1 second
        x2, y2, z2 = self.kepler_to_eci(keplerian, time_from_epoch + dt)
        vx = (x2 - x) / dt
        vy = (y2 - y) / dt
        vz = (z2 - z) / dt
        
        return {
            'x': x, 'y': y, 'z': z,
            'vx': vx, 'vy': vy, 'vz': vz,
            'altitude': altitude,
            'timestamp': target_time
        }
    
    def propagate_orbit(self, tle_line1: str, tle_line2: str,
                        start_time: datetime, duration_hours: int,
                        step_minutes: int = 5) -> List[Dict]:
        """
        Propagate orbit over time period
        """
        positions = []
        total_steps = duration_hours * 60 // step_minutes
        
        for step in range(total_steps):
            current_time = start_time + timedelta(minutes=step * step_minutes)
            position = self.calculate_position(tle_line1, tle_line2, current_time)
            positions.append(position)
        
        return positions
    
    

    from sgp4.api import Satrec, jday
from datetime import datetime


def propagate_satellite(tle_line1, tle_line2, dt=None):
    """
    Real SGP4 orbital propagation
    Returns position (km) and velocity (km/s)
    """

    if dt is None:
        dt = datetime.utcnow()

    satellite = Satrec.twoline2rv(tle_line1, tle_line2)

    jd, fr = jday(
        dt.year,
        dt.month,
        dt.day,
        dt.hour,
        dt.minute,
        dt.second + dt.microsecond * 1e-6
    )

    error_code, position, velocity = satellite.sgp4(jd, fr)

    if error_code != 0:
        return None

    return {
        "x": position[0],
        "y": position[1],
        "z": position[2],
        "vx": velocity[0],
        "vy": velocity[1],
        "vz": velocity[2],
    }