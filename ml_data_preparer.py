import pandas as pd
import numpy as np
from logging_setup import logger_main
from features import extract_features
from ml_data_preparer_utils import normalize_features
from data_utils import validate_data

def prepare_ml_data(data, lookback=10, lookforward=5):
    """Prepares data for ML training by extracting features and creating labels."""
    try:
        # Validate input data
        if not validate_data(data):
            logger_main.error("Invalid input data for ML preparation")
            return None, None, None, None

        # Extract features
        features = extract_features(data)
        if features is None or features.empty:
            logger_main.error("Failed to extract features for ML data")
            return None, None, None, None

        # Normalize features
        normalized_features = normalize_features(features)
        if normalized_features is None:
            logger_main.error("Failed to normalize features for ML data")
            return None, None, None, None

        # Create labels (future price movement: 1 for up, 0 for down)
        labels = []
        feature_rows = []
        for i in range(len(normalized_features) - lookforward):
            future_price = data['close'].iloc[i + lookforward]
            current_price = data['close'].iloc[i]
            label = 1 if future_price > current_price else 0
            labels.append(label)
            feature_row = normalized_features.iloc[i - lookback:i].values.flatten() if i >= lookback else None
            if feature_row is not None:
                feature_rows.append(feature_row)

        # Convert to numpy arrays
        X = np.array(feature_rows)
        y = np.array(labels[lookback:])  # Adjust labels to match feature rows

        # Split into train and test sets (80-20 split)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        logger_main.info(f"Prepared ML data: X_train={X_train.shape}, y_train={y_train.shape}, X_test={X_test.shape}, y_test={y_test.shape}")
        return X_train, y_train, X_test, y_test
    except Exception as e:
        logger_main.error(f"Error preparing ML data: {e}")
        return None, None, None, None

__all__ = ['prepare_ml_data']
