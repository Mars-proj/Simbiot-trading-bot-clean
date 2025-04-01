import pandas as pd
from logging_setup import logger_main

def validate_data(data):
    """Validates that the data is a non-empty DataFrame with required columns."""
    try:
        if not isinstance(data, pd.DataFrame):
            logger_main.error(f"Data must be a pandas DataFrame, got {type(data)}")
            return False
        if data.empty:
            logger_main.error("DataFrame is empty")
            return False
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        if not all(col in data.columns for col in required_columns):
            missing = [col for col in required_columns if col not in data.columns]
            logger_main.error(f"DataFrame missing required columns: {missing}")
            return False
        return True
    except Exception as e:
        logger_main.error(f"Error validating data: {e}")
        return False

def normalize_data(data):
    """Normalizes numerical columns in the DataFrame."""
    try:
        if not validate_data(data):
            return None
        numerical_columns = ['open', 'high', 'low', 'close', 'volume']
        normalized_data = data.copy()
        for col in numerical_columns:
            col_min = data[col].min()
            col_max = data[col].max()
            if col_max != col_min:  # Avoid division by zero
                normalized_data[col] = (data[col] - col_min) / (col_max - col_min)
            else:
                normalized_data[col] = 0  # If all values are the same, set to 0
        logger_main.info("Data normalized successfully")
        return normalized_data
    except Exception as e:
        logger_main.error(f"Error normalizing data: {e}")
        return None

__all__ = ['validate_data', 'normalize_data']
