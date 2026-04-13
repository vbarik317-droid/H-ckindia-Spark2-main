"""
Model trainer for LSTM satellite prediction models
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
from typing import Dict, List, Optional

from app.database.models import PositionHistory, Satellite, MLModelMetadata
from app.ml.lstm_model import SatelliteLSTMPredictor
from app.config import config

logger = logging.getLogger(__name__)

class ModelTrainer:
    """
    Trainer for LSTM models on satellite data
    """
    
    def __init__(self, db_session):
        self.db = db_session
        self.model_dir = 'ml_models/saved'
        os.makedirs(self.model_dir, exist_ok=True)
        
    def prepare_training_data(self, norad_id: str, days_back: int = 365) -> pd.DataFrame:


        # Get satellite
        satellite = self.db.query(Satellite).filter(
            Satellite.norad_id == norad_id
        ).first()

        if not satellite:
            logger.error(f"Satellite {norad_id} not found")
            return None

        # FIXED QUERY HERE 👇
        positions = self.db.query(PositionHistory).filter(
            PositionHistory.satellite_id == satellite.id,
            PositionHistory.data_source == 'actual'
        
        
        ).order_by(PositionHistory.timestamp).all()

        if len(positions) < config.SEQUENCE_LENGTH * 2:
            logger.warning(f"Insufficient data for {norad_id}: {len(positions)} points")
            return None

        data = []
        for pos in positions:
            data.append({
                'timestamp': pos.timestamp,
                'x': pos.pos_x,
                'y': pos.pos_y,
                'z': pos.pos_z
            })

        df = pd.DataFrame(data)

        # Drop rows with any NaNs
        df = df.dropna()

        if len(df) < config.SEQUENCE_LENGTH * 2:
            logger.error(
                f"Not enough clean numeric data after NaN removal: {len(df)} rows"
            )
            return None

        return df
    
    def train_satellite(self, norad_id: str, force_retrain: bool = False) -> bool:
        """
        Train model for a specific satellite
        """
        norad_id = str(norad_id)
        try:
            # Check if model already exists
            existing_model = self.db.query(MLModelMetadata).filter(
                MLModelMetadata.satellite_norad == norad_id,
                MLModelMetadata.is_active == True
            ).first()
            
            if existing_model and not force_retrain:
                logger.info(f"Model already exists for {norad_id}")
                return True
            
            predictor = SatelliteLSTMPredictor(
                model_dir=os.path.join(self.model_dir, norad_id)
            )
            predictor.sequence_length = config.SEQUENCE_LENGTH
            
            # Prepare data
            df = self.prepare_training_data(norad_id)
            if df is None or len(df) < 100:
                logger.warning(f"Insufficient data for {norad_id}")
                return False
            
            # Define features and targets
            feature_cols = ['x', 'y', 'z']
            target_cols  = ['x', 'y', 'z']
            
            # Train model
            predictor = SatelliteLSTMPredictor(
                model_dir=os.path.join(self.model_dir, norad_id)
            )
            
            history = predictor.train(
                df,
                feature_cols,
                target_cols,
                epochs=50,
                batch_size=32
            )
            
            if history is None:
                logger.error(f"Training failed for {norad_id}")
                return False
            
            # Save model
            predictor.save_model('best')
            
            # Store metadata
            val_loss = history.history.get('val_loss', [0])[-1]
            val_mae  = history.history.get('val_mae', [0])[-1]

            model_metadata = MLModelMetadata(
                model_version=f"v1_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                satellite_norad=norad_id,
                training_samples=len(df),
                validation_loss=float(val_loss),
                mean_absolute_error=float(val_mae),
                is_active=True,
                model_path=os.path.join(self.model_dir, norad_id, 'best_model.h5')
            )
            
            if existing_model:
                existing_model.is_active = False
            
            self.db.add(model_metadata)
            self.db.commit()
            
            logger.info(f"Model trained successfully for {norad_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error training model for {norad_id}: {e}")
            self.db.rollback()
            return False
    
    def train_all_satellites(self, force_retrain: bool = False) -> Dict:
        """
        Train models for all satellites with sufficient data
        """
        results = {
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }
        
        # Get all active satellites
        satellites = self.db.query(Satellite).filter(
            Satellite.is_active == True
        ).all()
        
        logger.info(f"Starting training for {len(satellites)} satellites")
        
        for sat in satellites:
            try:
                logger.info(f"Training model for {sat.norad_id} ({sat.name})")
                success = self.train_satellite(sat.norad_id, force_retrain)
                
                if success:
                    results['success'] += 1
                    results['details'].append({
                        'norad_id': sat.norad_id,
                        'name': sat.name,
                        'status': 'success'
                    })
                else:
                    results['failed'] += 1
                    results['details'].append({
                        'norad_id': sat.norad_id,
                        'name': sat.name,
                        'status': 'failed'
                    })
                    
            except Exception as e:
                logger.error(f"Error training {sat.norad_id}: {e}")
                results['failed'] += 1
                results['details'].append({
                    'norad_id': sat.norad_id,
                    'name': sat.name,
                    'status': 'error',
                    'error': str(e)
                })
        
        logger.info(f"Training complete: {results['success']} succeeded, {results['failed']} failed")
        return results