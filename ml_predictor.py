import pandas as pd
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from features import extract_features, calculate_sma, calculate_rsi

class Predictor:
    def __init__(self, retraining_manager):
        self.retraining_manager = retraining_manager
        self.model = self._build_model()

    def _build_model(self):
        model = Sequential([
            Dense(64, activation='relu', input_shape=(5,)),  # 5 features: returns, volatility, sma_20, sma_50, rsi
            Dense(32, activation='relu'),
            Dense(1)  # Output: predicted value
        ])
        model.compile(optimizer='adam', loss='mse')
        return model

    def predict(self, data):
        features = extract_features(data)
        sma = calculate_sma(data)
        rsi = calculate_rsi(data)
        
        # Prepare features for prediction
        feature_columns = ['returns', 'volatility', 'sma_20', 'sma_50', 'rsi']
        X = features[feature_columns].tail(1).to_numpy()  # Use the last row for prediction
        
        # Make prediction
        prediction = self.model.predict(X, verbose=0)
        return prediction[0][0]  # Return the predicted value
