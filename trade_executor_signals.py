import pandas as pd
import numpy as np
from logging_setup import logger_main
from signal_generator_indicators import calculate_rsi
from ohlcv_fetcher import fetch_ohlcv
from local_model_api import LocalModelAPI
from indicators import calculate_moving_average, calculate_bollinger_bands

async def process_signals(exchange_id, user_id, symbol, model_path=None, rsi_overbought=70, rsi_oversold=30, timeframe='1h', limit=100):
    """Processes trading signals using RSI, moving averages, Bollinger Bands, and ML predictions."""
    try:
        # Fetch OHLCV data
        ohlcv_data = await fetch_ohlcv(exchange_id, symbol, user_id, timeframe=timeframe, limit=limit, as_dataframe=True)
        if ohlcv_data is None or ohlcv_data.empty:
            logger_main.error(f"Failed to fetch OHLCV data for {symbol} on {exchange_id}")
            return None

        # Calculate RSI
        rsi = calculate_rsi(ohlcv_data['close'])
        latest_rsi = rsi.iloc[-1]

        # Calculate moving averages
        short_ma = calculate_moving_average(ohlcv_data['close'], window=20)
        long_ma = calculate_moving_average(ohlcv_data['close'], window=50)
        latest_short_ma = short_ma.iloc[-1]
        latest_long_ma = long_ma.iloc[-1]

        # Calculate Bollinger Bands
        upper_band, lower_band = calculate_bollinger_bands(ohlcv_data['close'])
        latest_upper_band = upper_band.iloc[-1]
        latest_lower_band = lower_band.iloc[-1]
        latest_price = ohlcv_data['close'].iloc[-1]

        # Initialize signals
        signals = []

        # RSI signal
        if latest_rsi > rsi_overbought:
            signals.append(('sell', 0.4))  # Sell signal with weight
        elif latest_rsi < rsi_oversold:
            signals.append(('buy', 0.4))  # Buy signal with weight

        # Moving average crossover signal
        if latest_short_ma > latest_long_ma:
            signals.append(('buy', 0.3))  # Bullish crossover
        elif latest_short_ma < latest_long_ma:
            signals.append(('sell', 0.3))  # Bearish crossover

        # Bollinger Bands signal
        if latest_price > latest_upper_band:
            signals.append(('sell', 0.3))  # Overbought
        elif latest_price < latest_lower_band:
            signals.append(('buy', 0.3))  # Oversold

        # ML prediction (if model is provided)
        ml_signal = None
        if model_path:
            try:
                model_api = LocalModelAPI(model_path)
                features = ohlcv_data[['open', 'high', 'low', 'close', 'volume']].tail(1).values
                ml_prediction = model_api.predict(features)
                if ml_prediction is not None:
                    ml_signal = 'buy' if ml_prediction > 0.5 else 'sell'
                    signals.append((ml_signal, 0.5))  # ML signal with higher weight
                else:
                    logger_main.warning(f"ML prediction failed for {symbol}, proceeding with indicator-based signals")
            except Exception as e:
                logger_main.error(f"Error in ML prediction for {symbol}: {e}, proceeding with indicator-based signals")

        # Aggregate signals
        if not signals:
            logger_main.info(f"No signals generated for {symbol} on {exchange_id}")
            return None

        buy_weight = sum(weight for signal, weight in signals if signal == 'buy')
        sell_weight = sum(weight for signal, weight in signals if signal == 'sell')

        # Determine final signal
        if buy_weight > sell_weight:
            final_signal = 'buy'
        elif sell_weight > buy_weight:
            final_signal = 'sell'
        else:
            logger_main.info(f"Signals are neutral for {symbol} on {exchange_id}: buy_weight={buy_weight}, sell_weight={sell_weight}")
            return None

        logger_main.info(f"Generated {final_signal} signal for {symbol} on {exchange_id}: buy_weight={buy_weight}, sell_weight={sell_weight}, RSI={latest_rsi}, MA_short={latest_short_ma}, MA_long={latest_long_ma}, Bollinger_upper={latest_upper_band}, Bollinger_lower={latest_lower_band}")
        return final_signal
    except Exception as e:
        logger_main.error(f"Error processing signals for {symbol} on {exchange_id}: {e}")
        return None

__all__ = ['process_signals']
