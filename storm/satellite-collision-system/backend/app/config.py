"""
Configuration module for environment variables and settings
"""
import os
from pathlib import Path

class Config:
    # Base directory
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:9691@localhost:5432/satellite_db")
    
    # API Keys
    CELESTRAK_URL = "https://celestrak.com/NORAD/elements/gp.php"
    SPACE_TRACK_USER = os.getenv("SPACE_TRACK_USER", "")
    SPACE_TRACK_PASS = os.getenv("SPACE_TRACK_PASS", "")
    N2YO_API_KEY = os.getenv("N2YO_API_KEY", "")
    
    # Application settings
    COLLISION_THRESHOLD_KM = 5.0  # High risk threshold
    PREDICTION_HOURS = 48  # Predict 48 hours ahead
    DATA_FETCH_INTERVAL = 300  # 5 minutes in seconds
    MODEL_RETRAIN_HOURS = 24  # Retrain every 24 hours
    
    # ML Model settings
    SEQUENCE_LENGTH = 24  # 24 time steps for LSTM
    N_FEATURES = 9  # [x, y, z, vx, vy, vz, inclination, eccentricity, altitude]
    N_TARGETS = 6  # [x, y, z, vx, vy, vz]
    
    # Simulation settings (for rate limits)
    SIMULATION_MODE = False
    

config = Config()