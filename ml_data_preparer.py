import pandas as pd
import numpy as np
from features import extract_features, normalize_data

def prepare_data(data, lookback=20):
    """
    Prepare data for ML model with feature extraction and normalization.

    Args:
        data (pd.DataFrame): OHLCV data.
        lookback (int): Lookback period for sequences (default: 20).

    Returns:
        tuple: (X, y) - Features and target.
    """
    X, y = [], []
    for i in range(lookback, len(data)):
        window = data.iloc[i-lookback:i+1]
        features = extract_features(window)
        X.append(features)
        y.append(1 if data['close'].iloc[i] > data['close'].iloc[i-1] else 0)
    
    X = np.array(X)
    y = np.array(y)
    
    # Нормализация
    X_df = pd.DataFrame(X)
    X_normalized = normalize_data(X_df)
    X = X_normalized.values
    
    return X, y
