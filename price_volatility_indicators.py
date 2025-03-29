import pandas as pd
import numpy as np
from logging_setup import logger_main

def calculate_bollinger_bands(data, period=20, std_dev=2):
    """Расчёт Bollinger Bands"""
    try:
        # Проверка входных данных
        if not isinstance(data, pd.DataFrame):
            logger_main.error(f"Некорректный тип данных для Bollinger Bands: {type(data)}")
            return pd.DataFrame()
        required_columns = ['close']
        if not all(col in data.columns for col in required_columns):
            logger_main.error(f"Отсутствуют необходимые колонки для Bollinger Bands: {data.columns}")
            return pd.DataFrame()
        if data.empty:
            logger_main.warning("Пустой DataFrame для Bollinger Bands")
            return pd.DataFrame()
        sma = data['close'].rolling(window=period).mean()
        std = data['close'].rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        bb = pd.DataFrame({
            'upper': upper,
            'middle': sma,
            'lower': lower
        })
        return bb
    except Exception as e:
        logger_main.error(f"Ошибка при расчёте Bollinger Bands: {str(e)}")
        return pd.DataFrame()

def calculate_atr(data, period=14):
    """Расчёт ATR (Average True Range)"""
    try:
        # Проверка входных данных
        if not isinstance(data, pd.DataFrame):
            logger_main.error(f"Некорректный тип данных для ATR: {type(data)}")
            return pd.Series()
        required_columns = ['high', 'low', 'close']
        if not all(col in data.columns for col in required_columns):
            logger_main.error(f"Отсутствуют необходимые колонки для ATR: {data.columns}")
            return pd.Series()
        if data.empty:
            logger_main.warning("Пустой DataFrame для ATR")
            return pd.Series()
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        # Заполняем NaN нулями
        atr = atr.fillna(0)
        logger_main.debug(f"ATR рассчитан, последнее значение: {atr.iloc[-1] if not atr.empty else 'пусто'}")
        return atr
    except Exception as e:
        logger_main.error(f"Ошибка при расчёте ATR: {str(e)}")
        return pd.Series()

def calculate_dynamic_atr_threshold(data, period=14, percentile=75):
    """Расчёт динамического порога ATR"""
    try:
        # Проверка входных данных
        if not isinstance(data, pd.DataFrame):
            logger_main.error(f"Некорректный тип данных для динамического порога ATR: {type(data)}")
            return pd.Series()
        required_columns = ['high', 'low', 'close']
        if not all(col in data.columns for col in required_columns):
            logger_main.error(f"Отсутствуют необходимые колонки для динамического порога ATR: {data.columns}")
            return pd.Series()
        if data.empty:
            logger_main.warning("Пустой DataFrame для динамического порога ATR")
            return pd.Series()
        atr = calculate_atr(data, period)
        threshold = atr.rolling(window=period).apply(lambda x: np.percentile(x, percentile), raw=True)
        # Заполняем NaN нулями
        threshold = threshold.fillna(0)
        logger_main.debug(f"Динамический порог ATR: {threshold.iloc[-1] if not threshold.empty else 'пусто'}")
        return threshold
    except Exception as e:
        logger_main.error(f"Ошибка при расчёте динамического порога ATR: {str(e)}")
        return pd.Series()

__all__ = ['calculate_bollinger_bands', 'calculate_atr', 'calculate_dynamic_atr_threshold']
