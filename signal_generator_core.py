import pandas as pd
import numpy as np
from logging_setup import logger_main
from utils import log_exception

async def generate_signals(ohlcv_data, timeframe='4h', symbol=None):
    """Генерирует торговые сигналы на основе OHLCV-данных"""
    logger_main.info(f"Generating signal for symbol: {symbol}")
    try:
        # Проверяем, что ohlcv_data — это список
        if not isinstance(ohlcv_data, list):
            logger_main.error(f"Invalid data type for {symbol}: {type(ohlcv_data)}")
            return None, {}

        # Преобразуем OHLCV-данные в DataFrame
        df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Рассчитываем индикаторы
        atr = calculate_atr(df)
        short_ma = df['close'].rolling(window=10).mean().iloc[-1] if len(df) >= 10 else 0
        long_ma = df['close'].rolling(window=50).mean().iloc[-1] if len(df) >= 50 else 0
        rsi = calculate_rsi(df)
        macd, macd_signal = calculate_macd(df)

        # Генерируем сигнал
        signal = 0
        if short_ma > long_ma and rsi < 70:
            signal = 1  # Buy
        elif short_ma < long_ma and rsi > 30:
            signal = -1  # Sell

        # Формируем метрики
        metrics = {
            'atr': atr,
            'short_ma': short_ma,
            'long_ma': long_ma,
            'rsi': rsi,
            'macd': macd,
            'macd_signal': macd_signal,
            'volatility': calculate_volatility(df)
        }

        return signal, metrics

    except Exception as e:
        logger_main.error(f"Error generating signal for {symbol}: {str(e)}")
        log_exception(f"Error generating signal: {str(e)}", e)
        return None, {}

def calculate_atr(df, period=14):
    """Рассчитывает ATR (Average True Range)"""
    if len(df) < period:
        return 0.0
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean().iloc[-1]
    return atr if not np.isnan(atr) else 0.0

def calculate_rsi(df, period=14):
    """Рассчитывает RSI (Relative Strength Index)"""
    if len(df) < period:
        return 0.0
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not np.isnan(rsi.iloc[-1]) else 0.0

def calculate_macd(df, fast=12, slow=26, signal=9):
    """Рассчитывает MACD и сигнальную линию"""
    if len(df) < slow:
        return 0.0, 0.0
    exp1 = df['close'].ewm(span=fast, adjust=False).mean()
    exp2 = df['close'].ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd.iloc[-1] if not np.isnan(macd.iloc[-1]) else 0.0, signal_line.iloc[-1] if not np.isnan(signal_line.iloc[-1]) else 0.0

def calculate_volatility(df, period=20):
    """Рассчитывает волатильность на основе стандартного отклонения"""
    if len(df) < period:
        return 0.0
    returns = df['close'].pct_change()
    volatility = returns.rolling(window=period).std().iloc[-1]
    return volatility if not np.isnan(volatility) else 0.0

__all__ = ['generate_signals']
