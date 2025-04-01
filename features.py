import pandas as pd
from logging_setup import logger_main
import os

def extract_features(data, rsi_period=14):
    """Extracts features from OHLCV data for ML models."""
    try:
        if not isinstance(data, pd.DataFrame):
            logger_main.error(f"Data must be a pandas DataFrame, got {type(data)}")
            return None
        if data.empty:
            logger_main.error("DataFrame is empty")
            return None

        # Calculate price changes
        features = pd.DataFrame(index=data.index)
        features['price_change'] = data['close'].pct_change()
        features['price_change_5'] = data['close'].pct_change(5)
        features['price_change_10'] = data['close'].pct_change(10)

        # Calculate moving averages
        features['ma_20'] = data['close'].rolling(window=20).mean()
        features['ma_50'] = data['close'].rolling(window=50).mean()

        # Calculate RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        features['rsi'] = 100 - (100 / (1 + rs))

        # Calculate volatility
        features['volatility'] = data['close'].rolling(window=20).std()

        # Drop NaN values
        features = features.dropna()
        logger_main.info(f"Extracted features for {len(features)} data points with RSI period {rsi_period}")
        return features
    except Exception as e:
        logger_main.error(f"Error extracting features: {e}")
        return None

__all__ = ['extract_features']
