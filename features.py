# features.py
import pandas as pd
import numpy as np
from logging_setup import logger_main

def extract_features(df, rsi_period=14):
    """
    Extracts features from historical OHLCV data.
    Args:
        df (pd.DataFrame): Historical OHLCV data with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        rsi_period (int): Period for RSI calculation
    Returns:
        pd.DataFrame: DataFrame with features including RSI and original 'close' column
    """
    try:
        logger_main.info(f"Extracting features for {len(df)} data points with RSI period {rsi_period}")
        
        # Проверяем наличие необходимых столбцов
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger_main.error(f"Missing required columns in DataFrame: {missing_columns}")
            return pd.DataFrame()

        # Копируем DataFrame, чтобы сохранить исходные данные
        features_df = df.copy()

        # Рассчитываем RSI
        delta = features_df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        features_df['rsi'] = 100 - (100 / (1 + rs))

        # Удаляем строки с NaN, которые появились из-за rolling
        features_df = features_df.dropna()

        logger_main.info(f"Extracted features for {len(features_df)} data points with RSI period {rsi_period}")
        logger_main.debug(f"Features DataFrame columns: {list(features_df.columns)}")
        return features_df

    except Exception as e:
        logger_main.error(f"Error extracting features: {e}")
        return pd.DataFrame()
