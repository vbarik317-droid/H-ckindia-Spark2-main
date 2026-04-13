"""
SQLAlchemy database models for satellite tracking system
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Satellite(Base):
    """Satellite master data"""
    __tablename__ = 'satellites'
    
    id = Column(Integer, primary_key=True)
    norad_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200))
    country = Column(String(100))
    launch_date = Column(DateTime, nullable=True)
    object_type = Column(String(50))  # PAYLOAD, ROCKET BODY, DEBRIS
    
    # Current TLE data
    tle_line1 = Column(Text)
    tle_line2 = Column(Text)
    epoch = Column(DateTime)
    
    # Orbital elements
    inclination = Column(Float)
    raan = Column(Float)  # Right Ascension of Ascending Node
    eccentricity = Column(Float)
    arg_perigee = Column(Float)
    mean_anomaly = Column(Float)
    mean_motion = Column(Float)  # revolutions per day
    
    # Current position (updated regularly)
    pos_x = Column(Float)  # km
    pos_y = Column(Float)
    pos_z = Column(Float)
    vel_x = Column(Float)  # km/s
    vel_y = Column(Float)
    vel_z = Column(Float)
    altitude = Column(Float)  # km
    
    # Data source tracking
    source = Column(String(50), default='unknown')  # spacetrack, celestrak, n2yo, simulated
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    is_active = Column(Boolean, default=True)

class PositionHistory(Base):
    """Historical position data for ML training"""
    __tablename__ = 'position_history'
    
    id = Column(Integer, primary_key=True)
    satellite_id = Column(Integer, index=True)
    norad_id = Column(String(50), index=True)
    timestamp = Column(DateTime, index=True)
    
    # Position and velocity
    pos_x = Column(Float)
    pos_y = Column(Float)
    pos_z = Column(Float)
    
    
    # Orbital elements at this time
    inclination = Column(Float)
    eccentricity = Column(Float)
    mean_motion = Column(Float)
    
    # Source of data (actual/predicted)
    data_source = Column(String(20), default='actual')
    
    created_at = Column(DateTime, server_default=func.now())

class TLEHistory(Base):
    """Historical TLE records"""
    __tablename__ = 'tle_history'
    
    id = Column(Integer, primary_key=True)
    norad_id = Column(String(50), index=True)
    tle_line1 = Column(Text)
    tle_line2 = Column(Text)
    epoch = Column(DateTime)
    fetch_time = Column(DateTime, server_default=func.now())
    source = Column(String(50), default='unknown')  # Track which API provided this TLE

class CollisionEvent(Base):
    """Detected collision events"""
    __tablename__ = 'collision_events'
    
    id = Column(Integer, primary_key=True)
    satellite1_norad = Column(String(50), index=True)
    satellite2_norad = Column(String(50), index=True)
    predicted_time = Column(DateTime)
    detected_at = Column(DateTime, server_default=func.now())
    
    # Collision details
    distance_km = Column(Float)
    probability = Column(Float)  # 0-1
    risk_level = Column(String(20))  # HIGH, MEDIUM, LOW
    
    # Position data at closest approach
    pos1_x = Column(Float)
    pos1_y = Column(Float)
    pos1_z = Column(Float)
    pos2_x = Column(Float)
    pos2_y = Column(Float)
    pos2_z = Column(Float)
    
    # Resolution
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)

class MLModelMetadata(Base):
    """Track ML model versions and performance"""
    __tablename__ = 'ml_models'
    
    id = Column(Integer, primary_key=True)
    model_version = Column(String(50), unique=True)
    satellite_norad = Column(String(50), index=True)
    trained_at = Column(DateTime, server_default=func.now())
    training_samples = Column(Integer)
    validation_loss = Column(Float)
    mean_absolute_error = Column(Float)  # in km
    is_active = Column(Boolean, default=False)
    model_path = Column(String(500))