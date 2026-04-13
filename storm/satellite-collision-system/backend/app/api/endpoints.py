# backend/app/api/endpoints.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
import logging

from ..core.database import SessionLocal
from ..services.tle_fetcher import TLEFetcher
from ..services.collision_detector import CollisionDetector
from ..services.ml_predictor import MLPredictor
from ..services.orbit_calculator import OrbitCalculator
from ..models.satellite import Satellite, CollisionEvent
from ..core.config import settings
from ..scheduler.tasks import fetch_all_tle_data

router = APIRouter()
logger = logging.getLogger(__name__)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

@router.post("/fetch-data")
async def fetch_data(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Trigger TLE data fetch"""
    try:
        background_tasks.add_task(fetch_all_tle_data)
        return {"message": "Data fetch started in background"}
    except Exception as e:
        logger.error(f"Error starting data fetch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/satellites")
async def get_satellites(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of tracked satellites"""
    satellites = db.query(Satellite).offset(skip).limit(limit).all()
    return satellites

@router.get("/satellites/{norad_id}/positions")
async def get_satellite_positions(
    norad_id: str,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get historical and predicted positions for a satellite"""
    calculator = OrbitCalculator()
    satellite = db.query(Satellite).filter(
        Satellite.norad_id == norad_id
    ).first()
    
    if not satellite:
        raise HTTPException(status_code=404, detail="Satellite not found")
    
    # Get actual positions from DB
    # ... (implementation)
    
    return {"positions": []}

@router.post("/train-model")
async def train_model(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Train ML models"""
    try:
        predictor = MLPredictor(db)
        background_tasks.add_task(predictor.train_models)
        return {"message": "Model training started"}
    except Exception as e:
        logger.error(f"Error starting model training: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predict/{norad_id}")
async def predict_positions(
    norad_id: str,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get predicted positions for a satellite"""
    predictor = MLPredictor(db)
    predictions = predictor.predict_positions(norad_id, hours)
    return {
        "norad_id": norad_id,
        "predictions": predictions,
        "confidence": 0.85  # Example confidence score
    }

@router.get("/collision-check")
async def check_collisions(
    hours_ahead: int = 24,
    db: Session = Depends(get_db)
):
    """Check for potential collisions"""
    detector = CollisionDetector(db)
    
    # Get active satellites
    satellites = db.query(Satellite).all()
    
    # Get predictions for all satellites
    predictor = MLPredictor(db)
    all_predictions = {}
    
    for sat in satellites[:10]:  # Limit for performance
        try:
            predictions = predictor.predict_positions(sat.norad_id, hours_ahead)
            if predictions:
                all_predictions[sat.norad_id] = predictions
        except Exception as e:
            logger.error(f"Error predicting for {sat.norad_id}: {e}")
    
    # Check collisions
    collisions = detector.predict_future_collisions(all_predictions, hours_ahead)
    
    return {
        "collisions": collisions,
        "total_checked": len(all_predictions),
        "timestamp": datetime.now()
    }

@router.get("/alerts")
async def get_collision_alerts(
    hours_back: int = 24,
    db: Session = Depends(get_db)
):
    """Get recent collision alerts"""
    cutoff = datetime.now() - timedelta(hours=hours_back)
    alerts = db.query(CollisionEvent).filter(
        CollisionEvent.detected_at >= cutoff,
        CollisionEvent.risk_level == 'HIGH'
    ).order_by(CollisionEvent.detected_at.desc()).all()
    
    return alerts

@router.post("/simulate-data")
async def simulate_data(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Generate simulated satellite data for testing"""
    from ..utils.data_simulator import DataSimulator
    
    simulator = DataSimulator()
    satellites = simulator.generate_satellite_data(count=50)
    
    # Store in database
    fetcher = TLEFetcher(db)
    await fetcher.store_satellite_data(satellites)
    
    return {"message": f"Generated {len(satellites)} simulated satellites"}