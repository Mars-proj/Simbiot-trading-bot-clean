from utils import logger_main, logger_debug
import pandas as pd
import numpy as np

# Кэш для результатов extract_features
features_cache = {}

def extract_features(df):
    cache_key = hash(df.to_string())
    if cache_key in features_cache:
        logger_debug.debug("Использован кэш для extract_features")
        return features_cache[cache_key]

    if len(df) < 20:  # Минимальная длина для скользящих средних
        logger_main.warning(f"Недостаточно данных для извлечения признаков: {len(df)} строк, требуется минимум 20")
        return None

    features = pd.DataFrame(index=df.index)
    features['returns'] = df['close'].pct_change().fillna(0)  # Заполняем NaN нулями
    features['rsi'] = compute_rsi(df['close'], 14)
    features['ma_short'] = df['close'].rolling(window=5, min_periods=1).mean()  # min_periods=1 для первых строк
    features['ma_long'] = df['close'].rolling(window=20, min_periods=1).mean()
    # Добавляем MACD
    exp1 = df['close'].ewm(span=12, adjust=False, min_periods=1).mean()
    exp2 = df['close'].ewm(span=26, adjust=False, min_periods=1).mean()
    features['macd'] = exp1 - exp2
    # Добавляем Bollinger Bands
    middle = df['close'].rolling(window=20, min_periods=1).mean()
    std = df['close'].rolling(window=20, min_periods=1).std()
    features['bb_upper'] = middle + 2 * std
    features['bb_lower'] = middle - 2 * std
    logger_debug.debug(f"Извлечены признаки: {list(features.columns)}")
    # Проверяем, сколько строк удалено dropna()
    original_len = len(df)
    features_cleaned = features
    if len(features_cleaned.dropna()) < original_len * 0.5:
        logger_debug.warning(f"Удалено больше 50% строк: {original_len} -> {len(features_cleaned.dropna())}")
    else:
        features_cleaned = features_cleaned.dropna()

    features_cache[cache_key] = features_cleaned
    return features_cleaned

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()
    rs = gain / (loss + 1e-10)  # Защита от деления на ноль
    return 100 - (100 / (1 + rs))
