import pandas as pd
import numpy as np
from utils import logger_main

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
        logger_main.debug("Импорт в indicators.py завершён")
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

def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
    """Расчёт MACD (Moving Average Convergence Divergence)"""
    try:
        # Проверка входных данных
        if not isinstance(data, pd.DataFrame):
            logger_main.error(f"Некорректный тип данных для MACD: {type(data)}")
            return pd.DataFrame()
        required_columns = ['close']
        if not all(col in data.columns for col in required_columns):
            logger_main.error(f"Отсутствуют необходимые колонки для MACD: {data.columns}")
            return pd.DataFrame()
        if data.empty:
            logger_main.warning("Пустой DataFrame для MACD")
            return pd.DataFrame()
        logger_main.debug(f"Расчёт MACD с fast_period={fast_period}, slow_period={slow_period}, signal_period={signal_period}")
        exp1 = data['close'].ewm(span=fast_period, adjust=False).mean()
        exp2 = data['close'].ewm(span=slow_period, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=signal_period, adjust=False).mean()
        macd_df = pd.DataFrame({
            'macd': macd,
            'signal': signal
        })
        logger_main.debug(f"MACD рассчитан, последние значения: macd={macd.iloc[-1] if not macd.empty else 'пусто'}, signal={signal.iloc[-1] if not signal.empty else 'пусто'}")
        return macd_df
    except Exception as e:
        logger_main.error(f"Ошибка при расчёте MACD: {str(e)}")
        return pd.DataFrame()

__all__ = ['calculate_rsi', 'calculate_macd']
