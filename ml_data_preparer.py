import pandas as pd
from logging_setup import logger_main
from features import extract_features
from ml_data_preparer_utils import normalize_data

async def prepare_data(data, for_retraining=False, rsi_period=14, future_periods=5, normalize_method='standard'):
    """Prepares data for ML models."""
    try:
        if not isinstance(data, dict):
            logger_main.error(f"Data must be a dictionary, got {type(data)}")
            return None
        if not data:
            logger_main.error("Input data is empty")
            return None

        # Convert data to DataFrame
        df = pd.DataFrame(data)
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                logger_main.error(f"Missing required column: {col}")
                return None

        # Extract features
        features = extract_features(df, rsi_period=rsi_period)
        if features is None:
            logger_main.error("Failed to extract features")
            return None

        # Normalize features
        normalized_features = normalize_data(features, method=normalize_method)
        if normalized_features is None:
            logger_main.error("Failed to normalize features")
            return None

        if for_retraining:
            # Add labels based on future price movement
            normalized_features['future_price'] = normalized_features['rsi'].shift(-future_periods)
            normalized_features['label'] = normalized_features.apply(
                lambda row: 1 if pd.notna(row['future_price']) and row['future_price'] > row['rsi'] else 0,
                axis=1
            )
            normalized_features = normalized_features.drop(columns=['future_price']).dropna()

        logger_main.info(f"Prepared data with shape: {normalized_features.shape}")
        return normalized_features
    except Exception as e:
        logger_main.error(f"Error preparing data: {e}")
        return None

__all__ = ['prepare_data']
