import pandas as pd
from logging_setup import logger_main

def normalize_features(features):
    """Normalizes features for ML training."""
    try:
        if not isinstance(features, pd.DataFrame):
            logger_main.error(f"Features must be a pandas DataFrame, got {type(features)}")
            return None
        if features.empty:
            logger_main.error("Features DataFrame is empty")
            return None

        normalized_features = features.copy()
        for column in normalized_features.columns:
            col_min = normalized_features[column].min()
            col_max = normalized_features[column].max()
            if col_max != col_min:  # Avoid division by zero
                normalized_features[column] = (normalized_features[column] - col_min) / (col_max - col_min)
            else:
                normalized_features[column] = 0  # If all values are the same, set to 0

        logger_main.info("Normalized features successfully")
        return normalized_features
    except Exception as e:
        logger_main.error(f"Error normalizing features: {e}")
        return None

__all__ = ['normalize_features']
