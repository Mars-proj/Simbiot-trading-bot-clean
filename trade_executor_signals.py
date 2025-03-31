import numpy as np
from logging_setup import logger_main
from signal_generator_indicators import calculate_rsi
from ohlcv_fetcher import fetch_ohlcv

async def process_signals(exchange_id, user_id, symbol, rsi_overbought=70, rsi_oversold=30, period=14):
    """Processes trading signals based on RSI with configurable thresholds."""
    try:
        # Fetch OHLCV data
        ohlcv = await fetch_ohlcv(exchange_id, symbol, timeframe='1h', limit=100)
        if ohlcv is None or len(ohlcv) == 0:
            logger_main.error(f"Failed to fetch OHLCV data for {symbol} on {exchange_id}")
            return None

        close_prices = np.array(ohlcv['close'])
        rsi = calculate_rsi(close_prices, period=period)
        if rsi is None:
            logger_main.error(f"Failed to calculate RSI for {symbol} on {exchange_id}")
            return None

        latest_rsi = rsi[-1]
        if latest_rsi > rsi_overbought:
            signal = 'sell'  # Overbought
        elif latest_rsi < rsi_oversold:
            signal = 'buy'   # Oversold
        else:
            signal = None    # Neutral

        logger_main.info(f"Processed signal for user {user_id} on {exchange_id} for {symbol}: RSI={latest_rsi}, signal={signal}")
        return signal
    except Exception as e:
        logger_main.error(f"Error processing signals for user {user_id} on {exchange_id} for {symbol}: {e}")
        return None

def aggregate_signals(signals, weights=None):
    """Aggregates signals from multiple sources with optional weights."""
    try:
        if not signals:
            logger_main.warning("No signals to aggregate")
            return None

        if not weights:
            weights = [1.0] * len(signals)  # Equal weights by default
        if len(weights) != len(signals):
            logger_main.error("Number of weights must match number of signals")
            return None

        buy_score = sum(w for s, w in zip(signals, weights) if s == "buy")
        sell_score = sum(w for s, w in zip(signals, weights) if s == "sell")

        if buy_score > sell_score:
            aggregated_signal = "buy"
        elif sell_score > buy_score:
            aggregated_signal = "sell"
        else:
            aggregated_signal = None  # Neutral if scores are equal

        logger_main.info(f"Aggregated signals: {signals} with weights {weights} -> {aggregated_signal}")
        return aggregated_signal
    except Exception as e:
        logger_main.error(f"Error aggregating signals: {e}")
        return None

__all__ = ['process_signals', 'aggregate_signals']
