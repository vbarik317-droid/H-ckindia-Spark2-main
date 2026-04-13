"""
LSTM model for satellite position prediction
Uses TensorFlow/Keras
"""
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.optimizers import Adam
import joblib
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class SatelliteLSTMPredictor:
    """
    LSTM-based predictor for satellite positions
    """
    
    def __init__(self, model_dir='ml_models/saved'):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)

        self.sequence_length = 24
        self.n_features = 3
        self.n_targets = 3

        self.model = None
        self.scaler_X = None
        self.scaler_y = None
        
    def build_model(self):
        """
        Build LSTM architecture
        """
        model = Sequential([
            # First LSTM layer
            LSTM(128, return_sequences=True, activation='tanh',
                 input_shape=(self.sequence_length, self.n_features)),
            Dropout(0.2),
            
            # Second LSTM layer
            LSTM(64, return_sequences=True, activation='tanh'),
            Dropout(0.2),
            
            # Third LSTM layer
            LSTM(32, return_sequences=False, activation='tanh'),
            Dropout(0.2),
            
            # Dense output layers
            Dense(64, activation='relu'),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dense(self.n_targets)
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        self.model = model
        return model
    
    def prepare_sequences(self, X, y):
        """
        Prepare sequences for LSTM training
        """
        X_seq, y_seq = [], []

        for i in range(len(X) - self.sequence_length):
            X_seq.append(X[i:i + self.sequence_length])
            y_seq.append(y[i + self.sequence_length])

        return np.array(X_seq), np.array(y_seq)
    def train(self, historical_data, feature_cols, target_cols,
          epochs=50, batch_size=32, validation_split=0.2):

        try:
            from sklearn.preprocessing import MinMaxScaler

            # 1️⃣ Dimensions
            self.n_features = len(feature_cols)
            self.n_targets = len(target_cols)

            # 2️⃣ Unique columns ONLY
            cols = list(dict.fromkeys(feature_cols + target_cols))
            df = historical_data[cols].copy()

            # 3️⃣ Force numeric safely
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            # 4️⃣ Drop NaNs once (keeps alignment)
            df = df.dropna()

            if len(df) < self.sequence_length * 2:
                raise ValueError("Not enough clean numeric data after NaN removal")

            # 5️⃣ Split features & targets
            X_raw = df[feature_cols].to_numpy(dtype=np.float32)
            y_raw = df[target_cols].to_numpy(dtype=np.float32)

            # 6️⃣ Scale
            self.scaler_X = MinMaxScaler()
            self.scaler_y = MinMaxScaler()

            X_scaled = self.scaler_X.fit_transform(X_raw)
            y_scaled = self.scaler_y.fit_transform(y_raw)

            # 7️⃣ Create sequences
            X_seq, y_seq = [], []
            for i in range(len(X_scaled) - self.sequence_length):
                X_seq.append(X_scaled[i:i + self.sequence_length])
                y_seq.append(y_scaled[i + self.sequence_length])

            X_seq = np.array(X_seq, dtype=np.float32)
            y_seq = np.array(y_seq, dtype=np.float32)

            # 8️⃣ Build model
            if self.model is None:
                self.model = self.build_model()

            # 9️⃣ Train
            history = self.model.fit(
                X_seq,
                y_seq,
                epochs=epochs,
                batch_size=batch_size,
                validation_split=validation_split,
                verbose=1
            )

            # 🔟 Save scalers
            joblib.dump(self.scaler_X, os.path.join(self.model_dir, "scaler_X.pkl"))
            joblib.dump(self.scaler_y, os.path.join(self.model_dir, "scaler_y.pkl"))

            return history

        except Exception as e:
            logger.error(f"Error in model training: {e}")
            return None
    
    def predict_next_steps(self, recent_sequence, n_steps=12):
        """
        Predict next n_steps positions
        """
        if self.scaler_X is None or self.scaler_y is None:
            logger.error("Scalers not loaded — cannot predict")
            return None
        
        
        if self.model is None:
            if not self.load_model():
                logger.error("No model loaded for prediction")
                return None
            
        
        
        try:
            predictions = []
            current_sequence = recent_sequence.copy()
            
            for _ in range(n_steps):
                # Scale current sequence
                current_scaled = self.scaler_X.transform(current_sequence)
                current_scaled = current_scaled.reshape(1, self.sequence_length, self.n_features)
                
                # Predict next step
                next_scaled = self.model.predict(current_scaled, verbose=0)
                
                # Inverse transform
                next_pred = self.scaler_y.inverse_transform(next_scaled)
                predictions.append(next_pred[0])
                
                # Update sequence for next prediction
                # Create new feature vector
                new_row = current_sequence[-1].copy()
                new_row[:self.n_targets] = next_pred[0]  # Update position/velocity
                current_sequence = np.vstack([current_sequence[1:], new_row])
                
            
            return np.array(predictions)
            
        except Exception as e:
            logger.error(f"Error in prediction: {e}")
            return None
    
    def load_model(self, version='best'):
        try:
            model_path = os.path.join(self.model_dir, f'{version}_model.h5')
            if not os.path.exists(model_path):
                logger.warning(f"Model file not found: {model_path}")
                return False

            # ✅ SAFE LOAD
            self.model = load_model(model_path, compile=False)

            # ✅ MANUAL COMPILE
            self.model.compile(
                optimizer=Adam(learning_rate=0.001),
                loss="mse",
                metrics=["mae"]
            )

            # ✅ LOAD SCALERS
            scaler_X_path = os.path.join(self.model_dir, 'scaler_X.pkl')
            scaler_y_path = os.path.join(self.model_dir, 'scaler_y.pkl')

            if not os.path.exists(scaler_X_path) or not os.path.exists(scaler_y_path):
                logger.error("Scaler files missing")
                return False

            self.scaler_X = joblib.load(scaler_X_path)
            self.scaler_y = joblib.load(scaler_y_path)

            logger.info(f"Model and scalers loaded from {self.model_dir}")
            return True

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def save_model(self, version='best'):
        """
        Save trained model
        """
        if self.model:
            model_path = os.path.join(self.model_dir, f'{version}_model.h5')
            self.model.save(model_path)
            logger.info(f"Model saved to {model_path}")
            return True
        return False