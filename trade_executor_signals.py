import numpy as np
import torch
from logging_setup import logger_main
from signal_generator_indicators import calculate_rsi
from ohlcv_fetcher import fetch_ohlcv
from local_model_api import LocalModelAPI

async def process_signals(exchange_id, user_id, symbol, model_path=None, rsi_overbought=70, rsi_oversold=30, period=14):
    """Processes trading signals based on RSI and optional ML model predictions."""
    try:
        # Fetch OHLCV data
        ohlcv = await fetch_ohlcv(exchange_id, symbol, timeframe='1h', limit=100)
        if ohlcv is None or len(ohlcv) == 0:
            logger_main.error(f"Failed to fetch OHLCV data for {symbol} on {exchange_id}")
            return None

        close_prices = np.array(ohlcv['close'])

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
                logger_main.warning(f"Failed to get ML prediction for {symbol}, using RSI signal only")

        # Aggregate signals
        signals = [s for s in [rsi_signal, ml_signal] if s is not None]
        if not signals:
            logger_main.warning(f"No valid signals for {symbol} on {exchange_id}")
            return None

        # Use weights: RSI has weight 0.6, ML has weight 0.4
        weights = [0.6 if s == rsi_signal else 0.4 for s in signals]
        final_signal = aggregate_signals(signals, weights)
        if final_signal is None:
            logger_main.warning(f"Neutral signal for {symbol} after aggregation")
            return None

        logger_main.info(f"Processed signal for user {user_id} on {exchange_id} for {symbol}: RSI={latest_rsi}, ML={ml_signal}, final_signal={final_signal}")
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
