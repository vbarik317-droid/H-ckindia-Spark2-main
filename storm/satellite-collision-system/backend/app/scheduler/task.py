"""
Scheduler tasks for automated data fetching and model training
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
from pytz import utc

from app.database.session import SessionLocal
from app.services.tle_fetcher import TLEFetcher
from app.services.collision_detector import CollisionDetector
from app.ml.trainer import ModelTrainer
from app.ml.predictor import MLPredictor
from app.config import config

from app.services.sgp4_propagator import propagate_tle
from app.database.models import PositionHistory


from app.database.models import Satellite, PositionHistory
from app.services.orbit_propagator import propagate_satellite

logger = logging.getLogger(__name__)

# Create scheduler
scheduler = BackgroundScheduler(timezone=utc)

def fetch_data_job():
    db = SessionLocal()

    satellites = db.query(Satellite).filter(
        Satellite.is_active == True
    ).limit(100).all()

    for sat in satellites:

        if not sat.tle_line1 or not sat.tle_line2:
            continue

        state = propagate_satellite(
            sat.tle_line1,
            sat.tle_line2
        )

        if state is None:
            continue

        # Store historical record
        position = PositionHistory(
            satellite_id=sat.id,
            timestamp=datetime.utcnow(),
            pos_x=state["x"],
            pos_y=state["y"],
            pos_z=state["z"],
            
        )

        db.add(position)

    # Update live position in Satellite table
    sat.pos_x = state["x"]
    sat.pos_y = state["y"]
    sat.pos_z = state["z"]
    sat.altitude = (
        (state["x"]**2 + state["y"]**2 + state["z"]**2)**0.5
    ) - 6371

    db.add(position)

    db.commit()
    db.close()

def train_models_job():
    """
    Job to retrain ML models
    """
    logger.info("Running scheduled model training")
    db = SessionLocal()
    try:
        trainer = ModelTrainer(db)
        results = trainer.train_all_satellites()
        logger.info(f"Model training complete: {results}")
    except Exception as e:
        logger.error(f"Error in train_models_job: {e}")
    finally:
        db.close()

def check_collisions_job():
    """
    Job to check for potential collisions
    """
    logger.info("Running scheduled collision check")
    db = SessionLocal()
    try:
        # Get active satellites
        from app.database.models import Satellite
        satellites = db.query(Satellite).filter(
            Satellite.is_active == True
        ).limit(100).all()
        
        # Get predictions
        predictor = MLPredictor(db)
        all_predictions = {}
        
        for sat in satellites:
            try:
                predictions = predictor.predict_satellite(sat.norad_id, 24)  # 24 hours ahead
                if predictions:
                    all_predictions[sat.norad_id] = predictions
            except Exception as e:
                logger.error(f"Error predicting for {sat.norad_id}: {e}")
        
        # Check collisions
        detector = CollisionDetector(db)
        collisions = detector.predict_future_collisions(all_predictions, 24)
        
        logger.info(f"Collision check complete: {len(collisions)} potential collisions")
        
    except Exception as e:
        logger.error(f"Error in check_collisions_job: {e}")
    finally:
        db.close()

def cleanup_old_data_job():
    """
    Job to clean up old data
    """
    logger.info("Running scheduled data cleanup")
    db = SessionLocal()
    try:
        from app.database.models import PositionHistory, TLEHistory
        from datetime import datetime, timedelta
        
        # Keep only last 90 days of position history
        cutoff = datetime.now() - timedelta(days=90)
        deleted = db.query(PositionHistory).filter(
            PositionHistory.timestamp < cutoff
        ).delete()
        
        # Keep only last 30 days of TLE history
        cutoff = datetime.now() - timedelta(days=30)
        deleted_tle = db.query(TLEHistory).filter(
            TLEHistory.fetch_time < cutoff
        ).delete()
        
        db.commit()
        logger.info(f"Cleanup complete: {deleted} positions, {deleted_tle} TLE records deleted")
        
    except Exception as e:
        logger.error(f"Error in cleanup job: {e}")
        db.rollback()
    finally:
        db.close()

def start_scheduler():
    """
    Initialize and start the scheduler with all jobs
    """
    # Clear any existing jobs
    scheduler.remove_all_jobs()
    
    # Add jobs
    scheduler.add_job(fetch_data_job, 'interval', minutes=5)
    
    scheduler.add_job(
        train_models_job,
        IntervalTrigger(hours=config.MODEL_RETRAIN_HOURS),
        id='train_models',
        replace_existing=True
    )
    
    scheduler.add_job(
        check_collisions_job,
        IntervalTrigger(minutes=15),  # Check every 15 minutes
        id='check_collisions',
        replace_existing=True
    )
    
    scheduler.add_job(
        cleanup_old_data_job,
        CronTrigger(hour=3, minute=0),  # Run at 3 AM daily
        id='cleanup_data',
        replace_existing=True
    )
    
    logger.info("Scheduler initialized with all jobs")
    
    # Start the scheduler
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")

# Initialize scheduler on module import
start_scheduler()