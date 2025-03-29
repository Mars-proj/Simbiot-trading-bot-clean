import pandas as pd
import numpy as np
from logging_setup import logger_main

def calculate_rsi(data, period=14):
    """Расчёт RSI (Relative Strength Index)"""
    try:
        # Проверка входных данных
        if not isinstance(data, pd.DataFrame):
            logger_main.error(f"Некорректный тип данных для RSI: {type(data)}")
            return pd.Series()
        required_columns = ['close']
        if not all(col in data.columns for col in required_columns):
            logger_main.error(f"Отсутствуют необходимые колонки для RSI: {data.columns}")
            return pd.Series()
        if data.empty:
            logger_main.warning("Пустой DataFrame для RSI")
            return pd.Series()
        logger_main.debug("Импорт в momentum_indicators.py завершён")
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        # Избегаем деления на ноль
        rs = gain / loss
        rs = rs.replace([np.inf, -np.inf], np.nan).fillna(0)
        rsi = 100 - (100 / (1 + rs))
        logger_main.debug(f"RSI рассчитан, последнее значение: {rsi.iloc[-1] if not rsi.empty else 'пусто'}")
        return rsi
    except Exception as e:
        logger_main.error(f"Ошибка при расчёте RSI: {str(e)}")
        return pd.Series()

def calculate_stochastic_oscillator(data, k_period=14, d_period=3):
    """Расчёт Stochastic Oscillator (%K и %D)"""
    try:
        # Проверка входных данных
        if not isinstance(data, pd.DataFrame):
            logger_main.error(f"Некорректный тип данных для Stochastic Oscillator: {type(data)}")
            return pd.DataFrame()
        required_columns = ['high', 'low', 'close']
        if not all(col in data.columns for col in required_columns):
            logger_main.error(f"Отсутствуют необходимые колонки для Stochastic Oscillator: {data.columns}")
            return pd.DataFrame()
        if data.empty:
            logger_main.warning("Пустой DataFrame для Stochastic Oscillator")
            return pd.DataFrame()
        # Рассчитываем %K
        lowest_low = data['low'].rolling(window=k_period).min()
        highest_high = data['high'].rolling(window=k_period).max()
        k = 100 * (data['close'] - lowest_low) / (highest_high - lowest_low)
        # Рассчитываем %D (скользящее среднее %K)
        d = k.rolling(window=d_period).mean()
        # Заполняем NaN нулями
        k = k.fillna(0)
        d = d.fillna(0)
        stochastic = pd.DataFrame({
            'k': k,
            'd': d
        })
        logger_main.debug(f"Stochastic Oscillator рассчитан, последние значения: %K={k.iloc[-1] if not k.empty else 'пусто'}, %D={d.iloc[-1] if not d.empty else 'пусто'}")
        return stochastic
    except Exception as e:
        logger_main.error(f"Ошибка при расчёте Stochastic Oscillator: {str(e)}")
        return pd.DataFrame()

__all__ = ['calculate_rsi', 'calculate_stochastic_oscillator']
