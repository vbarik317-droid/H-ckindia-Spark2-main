"""
Main FastAPI application for Satellite Collision Prediction System
"""
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 👇 ADD THESE IMPORTS
from app.api.routes.satellites import router as satellites_router
from app.api.routes.collisions import router as collisions_router
from app.api.routes.alerts import router as alerts_router



from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import logging 
from typing import List, Optional

from app.config import config
from app.database.session import SessionLocal, engine
from app.database.models import Base, Satellite, CollisionEvent
from app.services.tle_fetcher import TLEFetcher
from app.services.orbit_propagator import OrbitPropagator
from app.services.collision_detector import CollisionDetector
from app.services.data_simulator import DataSimulator
from app.services.real_data_fetcher import RealDataFetcher
from app.ml.trainer import ModelTrainer
from app.ml.predictor import MLPredictor
from app.scheduler.task import scheduler
from app.services.geo_utils import eci_to_latlon


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting Satellite Collision Prediction System")
    
    # Start scheduler
    if not scheduler.running:
        scheduler.start()
    logger.info("Scheduler started")
    
    yield
    
    # Shutdown
    scheduler.shutdown()
    logger.info("Scheduler stopped")

# Create FastAPI app
app = FastAPI(
    title="Satellite Collision Prediction API",
    description="AI-powered satellite tracking and collision prediction",
    version="1.0.0",
    lifespan=lifespan

    
)

# 👇 REGISTER ROUTES
app.include_router(satellites_router)
app.include_router(alerts_router)
app.include_router(collisions_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Satellite Collision Prediction System",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/fetch-real-data")
async def fetch_real_data(background_tasks: BackgroundTasks, db=Depends(get_db)):
    """
    Fetch REAL satellite data from authoritative sources:
    - Space-Track.org (official U.S. Space Surveillance Network) [citation:2]
    - CelesTrak (authoritative TLE data) [citation:1]
    - N2YO.com (real-time tracking) [citation:3]
    """
    try:
        fetcher = TLEFetcher(db)
        background_tasks.add_task(fetcher.fetch_and_store)
        
        return {
            "message": "Real data fetch started in background",
            "sources": ["Space-Track", "CelesTrak", "N2YO"],
            "note": "Rate limits apply: Space-Track (1/hour), N2YO (1000/day)"
        }
    except Exception as e:
        logger.error(f"Error starting real data fetch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/real-time-positions/{norad_id}")
async def get_real_time_positions(
    norad_id: str,
    seconds: int = 300,
    db=Depends(get_db)
):
    """
    Get real-time positions for a satellite from N2YO.com [citation:7]
    """
    try:
        fetcher = RealDataFetcher(db)
        positions = fetcher.get_satellite_positions(norad_id, 0, 0, seconds)
        
        if positions:
            return {
                "norad_id": norad_id,
                "positions": positions,
                "source": "N2YO.com"
            }
        else:
            raise HTTPException(status_code=404, detail="No position data available")
            
    except Exception as e:
        logger.error(f"Error getting real-time positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def simulate_data_task(db):
    """Background task for data simulation"""
    simulator = DataSimulator()
    satellites = simulator.generate_satellites(count=50)
    
    from app.database.models import Satellite
    for sat_data in satellites:
        satellite = Satellite(**sat_data)
        db.add(satellite)
    db.commit()
    logger.info(f"Simulated {len(satellites)} satellites")

@app.post("/api/v1/train-model")
async def train_model(background_tasks: BackgroundTasks, db=Depends(get_db)):
    """
    Train LSTM model on historical data
    """
    try:
        trainer = ModelTrainer(db)
        background_tasks.add_task(trainer.train_all_satellites)
        return {"message": "Model training started in background"}
    except Exception as e:
        logger.error(f"Error starting model training: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/satellites")
async def get_satellites(
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_db)
):
    satellites = db.query(Satellite).filter(
        Satellite.is_active == True
    ).offset(skip).limit(limit).all()

    results = []

    for s in satellites:

        if s.pos_x and s.pos_y and s.pos_z:
            lat, lon = eci_to_latlon(s.pos_x, s.pos_y, s.pos_z)
        else:
            lat, lon = None, None

        results.append({
            "norad_id": s.norad_id,
            "name": s.name,
            "object_type": s.object_type,
            "country": s.country,
            "altitude": s.altitude,
            "inclination": s.inclination,
            "latitude": lat,
            "longitude": lon,
            "source": s.source,  # real source from DB
            "updated_at": s.updated_at
        })

    return results

@app.get("/api/v1/satellites/{norad_id}/positions")
async def get_satellite_positions(
    norad_id: str,
    hours: int = 24,
    db=Depends(get_db)
):
    """
    Get historical positions for a satellite
    """
    from app.database.models import PositionHistory
    
    cutoff = datetime.now() - timedelta(hours=hours)
    positions = db.query(PositionHistory).filter(
        PositionHistory.norad_id == norad_id,
        PositionHistory.timestamp >= cutoff
    ).order_by(PositionHistory.timestamp).all()
    
    return [
    {
        "timestamp": p.timestamp,
        "pos_x": p.pos_x,
        "pos_y": p.pos_y,
        "pos_z": p.pos_z
    }
    for p in positions
]

@app.post("/api/v1/predict/{norad_id}")
async def predict_positions(
    norad_id: str,
    hours: int = 48,
    db=Depends(get_db)
):
    """
    Predict future positions for a satellite
    """
    try:
        predictor = MLPredictor(db)
        predictions = predictor.predict_satellite(norad_id, hours)
        
        if predictions is None:
            raise HTTPException(status_code=404, detail="Satellite not found or insufficient data")
        
        return {
            "norad_id": norad_id,
            "predictions": predictions,
            "confidence": 0.85,  # Example confidence score
            "model_version": "v1.0"
        }
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/collision-check")
async def check_collisions(
    hours_ahead: int = 48,
    db=Depends(get_db)
):
    """
    Check for potential collisions
    """
    try:
        # Get active satellites
        satellites = db.query(Satellite).filter(
            Satellite.is_active == True
        ).limit(20).all()  # Limit for performance
        
        # Get predictions for all satellites
        predictor = MLPredictor(db)
        all_predictions = {}
        
        for sat in satellites:
            try:
                predictions = predictor.predict_satellite(sat.norad_id, hours_ahead)
                if predictions:
                    all_predictions[sat.norad_id] = predictions
            except Exception as e:
                logger.error(f"Error predicting for {sat.norad_id}: {e}")
        
        # Check collisions
        detector = CollisionDetector(db)
        collisions = detector.predict_future_collisions(all_predictions, hours_ahead)
        
        return {
            "collisions": collisions,
            "total_checked": len(all_predictions),
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Collision check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/alerts")
async def get_alerts(
    hours_back: int = 24,
    risk_level: Optional[str] = None,
    db=Depends(get_db)
):
    """
    Get recent collision alerts
    """
    cutoff = datetime.now() - timedelta(hours=hours_back)
    query = db.query(CollisionEvent).filter(
        CollisionEvent.detected_at >= cutoff,
        CollisionEvent.is_resolved == False
    )
    
    if risk_level:
        query = query.filter(CollisionEvent.risk_level == risk_level.upper())
    
    alerts = query.order_by(CollisionEvent.detected_at.desc()).all()
    
    return [
    {
        "id": a.id,
        "satellite1_norad": a.satellite1_norad,
        "satellite1_name": db.query(Satellite.name).filter(Satellite.norad_id == a.satellite1_norad).scalar(),
        "satellite2_norad": a.satellite2_norad,
        "satellite2_name": db.query(Satellite.name).filter(Satellite.norad_id == a.satellite2_norad).scalar(),
        "predicted_time": a.predicted_time,
        "distance_km": a.distance_km,
        "probability": a.probability,
        "risk_level": a.risk_level,
        "detected_at": a.detected_at
    }
    for a in alerts
]

@app.post("/api/v1/simulate-data")
async def simulate_data(
    count: int = 50,
    db=Depends(get_db)
):
    """
    Generate simulated satellite data for testing
    """
    simulator = DataSimulator()
    satellites = simulator.generate_satellites(count)
    
    from app.database.models import Satellite
    for sat_data in satellites:
        satellite = Satellite(**sat_data)
        db.add(satellite)
    db.commit()
    
    return {"message": f"Generated {len(satellites)} simulated satellites"}

@app.post("/api/v1/add-test-alert")
async def add_test_alert(db=Depends(get_db)):
    """
    Add a test collision alert
    """

    test_alert = CollisionEvent(
        satellite1_norad="25544",
        satellite2_norad="40967",
        predicted_time=datetime.now() + timedelta(hours=5),
        distance_km=0.42,
        probability=0.87,
        risk_level="HIGH",
        detected_at=datetime.now(),
        is_resolved=False
    )

    db.add(test_alert)
    db.commit()

    return {"message": "Test collision alert added"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)