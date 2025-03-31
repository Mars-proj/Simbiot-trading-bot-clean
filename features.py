import pandas as pd
from logging_setup import logger_main

def extract_features(data, rsi_period=14):
    """Extracts features from OHLCV data for ML models."""
    try:
        if not isinstance(data, pd.DataFrame):
            logger_main.error(f"Data must be a pandas DataFrame, got {type(data)}")
            return None
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in data.columns:
                logger_main.error(f"Missing required column: {col}")
                return None

        features = pd.DataFrame(index=data.index)
        features['price_change'] = data['close'].pct_change()
        features['volatility'] = data['close'].rolling(window=rsi_period).std()
        features['rsi'] = calculate_rsi(data['close'], period=rsi_period)
        features = features.dropna()
        logger_main.info(f"Extracted features: {list(features.columns)}")
        return features
    except Exception as e:
        logger_main.error(f"Error extracting features: {e}")
        return None

def calculate_rsi(series, period=14):
    """Calculates RSI for a series."""
    try:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-10)  # Avoid division by zero
        rsi = 100 - (100 / (1 + rs))
        return rsi
    except Exception as e:
        logger_main.error(f"Error calculating RSI: {e}")
        return None

__all__ = ['extract_features', 'calculate_rsi']
