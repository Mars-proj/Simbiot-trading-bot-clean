# ml_data_preparer.py
import pandas as pd
import numpy as np
from logging_setup import logger_main

def prepare_ml_data(df, trade_data):
    """
    Prepares machine learning data from historical OHLCV data and trade data.
    Args:
        df (pd.DataFrame): Historical OHLCV data with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        trade_data (list): List of trade data entries, each entry is a dict with 'price' key
    Returns:
        tuple: (X, y) where X is the feature matrix and y is the target vector
    """
    try:
        logger_main.info(f"Preparing ML data with {len(df)} data points")
        
        # Extract features (e.g., RSI, moving averages)
        from features import extract_features
        features_df = extract_features(df, rsi_period=14)
        if features_df.empty:
            logger_main.error("Failed to extract features for ML data")
            return None, None

        # Normalize features
        from ml_data_preparer_utils import normalize_features
        normalized_features = normalize_features(features_df)
        if normalized_features is None:
            logger_main.error("Failed to normalize features for ML data")
            return None, None

        # Prepare target variable (e.g., price direction)
        y = []
        # Проверяем trade_data
        if not trade_data or not isinstance(trade_data, list):
            logger_main.error("trade_data is empty or not a list")
            # Если trade_data пустое, используем альтернативный способ определения y
            for i in range(len(normalized_features) - 1):
                # Сравниваем текущую цену закрытия со следующей
                if normalized_features['close'].iloc[i] <= normalized_features['close'].iloc[i + 1]:
                    y.append(1)  # Price goes up
                else:
                    y.append(0)  # Price goes down
        else:
            # Извлечём цену последней сделки из trade_data
            last_trade_price = trade_data[-1].get('price', 0) if isinstance(trade_data[-1], dict) else 0
            for i in range(len(normalized_features) - 1):
                # Сравниваем с ценой последней сделки
                if normalized_features['close'].iloc[i] >= last_trade_price:
                    y.append(1)  # Price goes up
                else:
                    y.append(0)  # Price goes down

        X = normalized_features.iloc[:-1].values
        y = np.array(y)

        logger_main.info(f"Prepared ML data: X shape {X.shape}, y shape {y.shape}")
        return X, y

    except Exception as e:
        logger_main.error(f"Error preparing ML data: {e}")
        return None, None
