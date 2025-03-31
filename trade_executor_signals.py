import numpy as np
import torch
import pandas as pd
from logging_setup import logger_main
from signal_generator_indicators import calculate_rsi
from ohlcv_fetcher import fetch_ohlcv
from local_model_api import LocalModelAPI
from indicators import calculate_moving_average, calculate_bollinger_bands

async def process_signals(exchange_id, user_id, symbol, model_path=None, rsi_overbought=70, rsi_oversold=30, period=14, ma_window=20, bb_window=20, bb_std=2):
    """Processes trading signals based on RSI, moving averages, Bollinger Bands, and optional ML model predictions."""
    try:
        # Fetch OHLCV data
        ohlcv = await fetch_ohlcv(exchange_id, symbol, user_id, timeframe='1h', limit=100, as_dataframe=True)
        if ohlcv is None or len(ohlcv) == 0:
            logger_main.error(f"Failed to fetch OHLCV data for {symbol} on {exchange_id}")
            return None

        close_prices = ohlcv['close'].values
        df = ohlcv

        # Calculate RSI signal
        rsi = calculate_rsi(close_prices, period=period)
        if rsi is None:
            logger_main.error(f"Failed to calculate RSI for {symbol} on {exchange_id}")
            return None

        latest_rsi = rsi[-1]
        rsi_signal = None
        if latest_rsi > rsi_overbought:
            rsi_signal = 'sell'  # Overbought
        elif latest_rsi < rsi_oversold:
            rsi_signal = 'buy'   # Oversold

        # Calculate Moving Average signal
        ma = calculate_moving_average(df['close'], window=ma_window)
        if ma is None:
            logger_main.error(f"Failed to calculate moving average for symbol {symbol}")
            return None
        latest_ma = ma.iloc[-1]
        latest_price = df['close'].iloc[-1]
        ma_signal = 'buy' if latest_price > latest_ma else 'sell'

        # Calculate Bollinger Bands signal
        upper_band, middle_band, lower_band = calculate_bollinger_bands(df['close'], window=bb_window, num_std=bb_std)
        if upper_band is None or middle_band is None or lower_band is None:
            logger_main.error(f"Failed to calculate Bollinger Bands for symbol {symbol}")
            return None
        latest_upper = upper_band.iloc[-1]
        latest_lower = lower_band.iloc[-1]
        bb_signal = None
        if latest_price > latest_upper:
            bb_signal = 'sell'  # Overbought
        elif latest_price < latest_lower:
            bb_signal = 'buy'   # Oversold

        # Calculate ML signal if model is provided
        ml_signal = None
        if model_path:
            model_api = LocalModelAPI(model_path)
            # Prepare input data for ML model (example: last 10 closing prices)
            input_data = torch.tensor(close_prices[-10:], dtype=torch.float32).unsqueeze(0)  # Shape: (1, 10)
            prediction = model_api.predict(input_data)
            if prediction is not None:
                # Assume prediction > 0.5 means buy, < 0.5 means sell
                ml_signal = 'buy' if prediction.item() > 0.5 else 'sell'
                logger_main.info(f"ML prediction for {symbol}: {prediction.item()}, signal={ml_signal}")
            else:
                logger_main.warning(f"Failed to get ML prediction for {symbol}, using other signals")

        # Aggregate signals
        signals = [s for s in [rsi_signal, ma_signal, bb_signal, ml_signal] if s is not None]
        if not signals:
            logger_main.warning(f"No valid signals for {symbol} on {exchange_id}")
            return None

        # Use weights: RSI (0.4), MA (0.2), BB (0.2), ML (0.2)
        weights = []
        for s in signals:
            if s == rsi_signal:
                weights.append(0.4)
            elif s == ma_signal:
                weights.append(0.2)
            elif s == bb_signal:
                weights.append(0.2)
            elif s == ml_signal:
                weights.append(0.2)

        final_signal = aggregate_signals(signals, weights)
        if final_signal is None:
            logger_main.warning(f"Neutral signal for {symbol} after aggregation")
            return None

        logger_main.info(f"Processed signal for user {user_id} on {exchange_id} for {symbol}: RSI={latest_rsi}, MA={ma_signal}, BB={bb_signal}, ML={ml_signal}, final_signal={final_signal}")
        return final_signal
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
