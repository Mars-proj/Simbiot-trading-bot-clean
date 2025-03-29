import pandas as pd
import numpy as np
from logging_setup import logger_main

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

def calculate_adx(data, period=14):
    """Расчёт ADX (Average Directional Index)"""
    try:
        # Проверка входных данных
        if not isinstance(data, pd.DataFrame):
            logger_main.error(f"Некорректный тип данных для ADX: {type(data)}")
            return pd.Series()
        required_columns = ['high', 'low', 'close']
        if not all(col in data.columns for col in required_columns):
            logger_main.error(f"Отсутствуют необходимые колонки для ADX: {data.columns}")
            return pd.Series()
        if data.empty:
            logger_main.warning("Пустой DataFrame для ADX")
            return pd.Series()
        # Рассчитываем +DM и -DM
        up_move = data['high'].diff()
        down_move = -data['low'].diff()
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        # Рассчитываем TR (True Range)
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        tr = tr.rolling(window=period).mean()
        # Сглаживаем +DM, -DM и TR
        plus_dm = pd.Series(plus_dm).rolling(window=period).mean()
        minus_dm = pd.Series(minus_dm).rolling(window=period).mean()
        tr = tr.rolling(window=period).mean()
        # Рассчитываем +DI и -DI
        plus_di = 100 * (plus_dm / tr)
        minus_di = 100 * (minus_dm / tr)
        # Рассчитываем DX
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        # Рассчитываем ADX
        adx = pd.Series(dx).rolling(window=period).mean()
        # Заполняем NaN нулями
        adx = adx.fillna(0)
        logger_main.debug(f"ADX рассчитан, последнее значение: {adx.iloc[-1] if not adx.empty else 'пусто'}")
        return adx
    except Exception as e:
        logger_main.error(f"Ошибка при расчёте ADX: {str(e)}")
        return pd.Series()

__all__ = ['calculate_macd', 'calculate_adx']
