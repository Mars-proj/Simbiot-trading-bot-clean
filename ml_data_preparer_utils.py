from logging_setup import logger_main
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler

def normalize_data(data, method='standard'):
    """Normalizes data for ML models with a specified method."""
    try:
        if not isinstance(data, pd.DataFrame):
            logger_main.error(f"Data must be a pandas DataFrame, got {type(data)}")
            return None
        if method not in ['standard', 'minmax']:
            logger_main.error(f"Invalid normalization method {method}: must be 'standard' or 'minmax'")
            return None

        if method == 'standard':
            scaler = StandardScaler()
        else:  # minmax
            scaler = MinMaxScaler()

        normalized_data = pd.DataFrame(scaler.fit_transform(data), columns=data.columns, index=data.index)
        logger_main.info(f"Data normalized successfully using {method} method")
        return normalized_data
    except Exception as e:
        logger_main.error(f"Error normalizing data: {e}")
        return None

__all__ = ['normalize_data']
