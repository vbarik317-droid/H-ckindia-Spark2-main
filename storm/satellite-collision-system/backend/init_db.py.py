"""
Database initialization script
Run this to create tables and initial data
"""
from app.database.session import engine
from app.database.models import Base
from app.services.data_simulator import DataSimulator
from app.database.session import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize database with tables and sample data"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # Add sample data if empty
    db = SessionLocal()
    try:
        from app.database.models import Satellite
        count = db.query(Satellite).count()
        
        if count == 0:
            logger.info("No satellites found, generating sample data...")
            simulator = DataSimulator()
            satellites = simulator.generate_satellites(50)
            
            for sat_data in satellites:
                satellite = Satellite(**sat_data)
                db.add(satellite)
            
            db.commit()
            logger.info(f"Added {len(satellites)} sample satellites")
        else:
            logger.info(f"Database already has {count} satellites")
            
    finally:
        db.close()

if __name__ == "__main__":
    init_database()