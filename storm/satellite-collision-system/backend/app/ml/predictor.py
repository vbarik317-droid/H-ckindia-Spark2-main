"""
ML Predictor service for satellite position prediction
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
from typing import List, Dict, Optional

from app.database.models import Satellite, PositionHistory, MLModelMetadata
from app.ml.lstm_model import SatelliteLSTMPredictor
from app.services.orbit_propagator import OrbitPropagator
from app.config import config
from app.ml.trainer import ModelTrainer


from typing import List, Dict
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class MLPredictor:
    """
    Service for making predictions using trained LSTM models
    """
    
    def __init__(self, db_session):
        self.db = db_session
        self.model_dir = 'ml_models/saved'
        self.propagator = OrbitPropagator()
        
    def get_latest_model(self, norad_id: str) -> Optional[str]:
        """
        Get path to latest model for a satellite
        """
        model_meta = self.db.query(MLModelMetadata).filter(
            MLModelMetadata.satellite_norad == norad_id,
            MLModelMetadata.is_active == True
        ).order_by(MLModelMetadata.trained_at.desc()).first()
        
        if model_meta and os.path.exists(model_meta.model_path):
            return model_meta.model_path
        return None
    
    def prepare_sequence(self, norad_id: str, sequence_length: int = 24) -> Optional[np.ndarray]:
        """
        Prepare recent sequence for prediction
        """
        # Get recent positions
        satellite = self.db.query(Satellite).filter(
            Satellite.norad_id == norad_id
        ).first()

        satellite = self.db.query(Satellite).filter(
            Satellite.norad_id == norad_id
        ).first()

        if not satellite:
            return None

        positions = self.db.query(PositionHistory).filter(
            PositionHistory.satellite_id == satellite.id,
            PositionHistory.data_source == 'actual'
        ).order_by(PositionHistory.timestamp.desc()).limit(sequence_length + 5).all()
        
        if len(positions) < sequence_length:
            logger.warning(f"Insufficient recent data for {norad_id}")
            return None
        
        # Sort chronologically
        positions = sorted(positions, key=lambda x: x.timestamp)
        positions = positions[-sequence_length:]
        
        # Get satellite for constant elements
        satellite = self.db.query(Satellite).filter(
            Satellite.norad_id == norad_id
        ).first()
        
        if not satellite:
            return None
        
        # Build sequence
        sequence = []
        for pos in positions:
            sequence.append([
                pos.pos_x, pos.pos_y, pos.pos_z,
            ])
        
        return np.array(
            [[p.pos_x, p.pos_y, p.pos_z] for p in positions],
            dtype=np.float32
        )
    
    def predict_satellite(self, norad_id: str, hours_ahead: int = 48) -> Optional[List[Dict]]:
        """
        Predict future positions for a satellite
        """
        try:
            # Check if satellite exists
            satellite = self.db.query(Satellite).filter(
                Satellite.norad_id == norad_id
            ).first()
            
            if not satellite:
                logger.error(f"Satellite {norad_id} not found")
                return None
            
            # Try ML prediction first
            model_path = self.get_latest_model(norad_id)
            
            if model_path and os.path.exists(model_path):
                logger.info(f"Using ML model for {norad_id}")
                
                # Prepare sequence
                sequence = self.prepare_sequence(norad_id, config.SEQUENCE_LENGTH)
                
                if sequence is not None:
                    # Load predictor
                    predictor = SatelliteLSTMPredictor(
                        model_dir=os.path.dirname(model_path)
                    )
                    model_path = self.get_latest_model(norad_id)
                    predictor = SatelliteLSTMPredictor(
                        model_dir=os.path.dirname(model_path)
                    )

                    predictor.sequence_length = config.SEQUENCE_LENGTH
                    predictor.load_model('best')
                    
                    # Make predictions
                    n_steps = hours_ahead * 60 // 5  # 5-minute steps
                    predictions = predictor.predict_next_steps(sequence, n_steps)
                    
                    if predictions is not None:
                        # Format results
                        results = []
                        last_known = self.db.query(PositionHistory).filter(
                            PositionHistory.satellite_id == satellite.id,
                            PositionHistory.data_source == 'actual'
                        ).order_by(PositionHistory.timestamp.desc()).first()

                        # 🔥 GLOBAL TIME GRID (CRITICAL FOR COLLISIONS)
                        last_time = datetime.utcnow().replace(second=0, microsecond=0)
                        
                        for i, pred in enumerate(predictions):
                            pred_time = last_time + timedelta(minutes=5 * (i + 1))
                            results.append({
                                'timestamp': pred_time,
                                'x': float(pred[0]),
                                'y': float(pred[1]),
                                'z': float(pred[2]),
                                'source': 'ml_prediction'
                            })
                        self.save_predictions_to_db(satellite, results)
                        
                        return results
            
            # Fallback to orbit propagation
            # If no ML model found → force training

            trainer = ModelTrainer(self.db)
            trainer.train_satellite(norad_id, force_retrain=True)

            # Try again after training
            model_path = self.get_latest_model(norad_id)

            if model_path and os.path.exists(model_path):
                predictor = SatelliteLSTMPredictor(
                    model_dir=os.path.dirname(model_path)
                )
                predictor.load_model()

                sequence = self.prepare_sequence(norad_id, config.SEQUENCE_LENGTH)

                if sequence is not None:
                    n_steps = hours_ahead * 60 // 5
                    predictions = predictor.predict_next_steps(sequence, n_steps)
                    if predictions is None:
                        return None

                    results = []
                    # 🔥 GLOBAL TIME GRID (CRITICAL FOR COLLISIONS)
                    last_time = datetime.utcnow().replace(second=0, microsecond=0)

                    for i, pred in enumerate(predictions):
                        pred_time = last_time + timedelta(minutes=5 * (i + 1))
                        results.append({
                            'timestamp': pred_time,
                            'x': float(pred[0]),
                            'y': float(pred[1]),
                            'z': float(pred[2]),
                            'source': 'ml_prediction'
                        })

                    return results
                
        except Exception as e:
            logger.error(f"Error predicting for {norad_id}: {e}")
            return None
    
    def predict_batch(self, norad_ids: List[str], hours_ahead: int = 48) -> Dict:
        """
        Predict for multiple satellites
        """
        results = {}
        
        for norad_id in norad_ids:
            try:
                predictions = self.predict_satellite(norad_id, hours_ahead)
                if predictions:
                    results[norad_id] = predictions
            except Exception as e:
                logger.error(f"Error in batch prediction for {norad_id}: {e}")
                results[norad_id] = None
        
        return results
    
    def save_predictions_to_db(self, satellite, predictions):
        try:
            if not satellite.norad_id:
                raise ValueError("Satellite norad_id is NULL – refusing to save ML predictions")

            self.db.query(PositionHistory).filter(
                PositionHistory.satellite_id == satellite.id,
                PositionHistory.data_source == "ml_prediction"
            ).delete()

            records = []

            for pred in predictions:
                records.append(
                    PositionHistory(
                        satellite_id=satellite.id,
                        norad_id=str(satellite.norad_id),  # ✅ FORCE STRING
                        timestamp=pred["timestamp"],
                        pos_x=pred["x"],
                        pos_y=pred["y"],
                        pos_z=pred["z"],
                        data_source="ml_prediction"
                    )
                )

            self.db.bulk_save_objects(records)
            self.db.commit()

            print(f"[ML] Saved {len(records)} predictions for NORAD {satellite.norad_id}")

        except Exception as e:
            self.db.rollback()
            print(f"[ML][FATAL] Prediction save blocked: {e}")