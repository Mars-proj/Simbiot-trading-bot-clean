import pandas as pd
import numpy as np
import cupy as cp
from logging_setup import logger_main
from price_volatility_indicators import calculate_atr
from momentum_indicators import calculate_rsi
from trend_indicators import calculate_macd
from redis_initializer import redis_client

async def calculate_indicators_and_signal(ohlcv, symbol, volatility, rsi_buy, rsi_sell, short_window, long_window, volatility_threshold, success_prob):
    if redis_client is None:
        logger_main.error("redis_client is not initialized")
        raise ValueError("redis_client is not initialized")
    try:
        # ATR
        atr_cache_key = f"indicator:atr:{symbol}:4h"
        cached_atr = await redis_client.get_json(atr_cache_key)
        if cached_atr is not None:
            atr_value = cached_atr
        else:
            atr = calculate_atr(ohlcv, period=14)
            atr_value = atr.iloc[-1] if not atr.empty and not np.isnan(atr.iloc[-1]) else 0.0
            if atr.empty or np.isnan(atr_value):
                logger_main.info(f"Failed to calculate ATR for {symbol}")
            await redis_client.set_json(atr_cache_key, atr_value, expire=300)

        # Moving Averages
        short_ma_cache_key = f"indicator:short_ma:{symbol}:4h:{short_window}"
        long_ma_cache_key = f"indicator:long_ma:{symbol}:4h:{long_window}"
        cached_short_ma = await redis_client.get_json(short_ma_cache_key)
        cached_long_ma = await redis_client.get_json(long_ma_cache_key)
        if cached_short_ma is not None and cached_long_ma is not None:
            latest_short_ma = cached_short_ma
            latest_long_ma = cached_long_ma
        else:
            close = cp.array(ohlcv['close'].values)
            short_ma = cp.mean(close[-short_window:])
            long_ma = cp.mean(close[-long_window:])
            if len(ohlcv) < long_window:
                logger_main.info(f"Insufficient data for MA for {symbol} ({len(ohlcv)} < {long_window})")
                return 0, {'atr': atr_value, 'short_ma': 0.0, 'long_ma': 0.0, 'rsi': 0.0, 'macd': 0.0, 'macd_signal': 0.0}
            latest_short_ma = float(cp.asnumpy(short_ma))
            latest_long_ma = float(cp.asnumpy(long_ma))
            await redis_client.set_json(short_ma_cache_key, latest_short_ma, expire=300)
            await redis_client.set_json(long_ma_cache_key, latest_long_ma, expire=300)

        latest_close = ohlcv['close'].iloc[-1]
        if np.isnan(latest_short_ma) or np.isnan(latest_long_ma) or np.isnan(latest_close):
            logger_main.info(f"NaN in moving averages for {symbol}")
            return 0, {'atr': atr_value, 'short_ma': 0.0, 'long_ma': 0.0, 'rsi': 0.0, 'macd': 0.0, 'macd_signal': 0.0}

        # RSI
        rsi_cache_key = f"indicator:rsi:{symbol}:4h"
        cached_rsi = await redis_client.get_json(rsi_cache_key)
        if cached_rsi is not None:
            rsi_value = cached_rsi
        else:
            close_df = pd.DataFrame({'close': ohlcv['close']})
            rsi = calculate_rsi(close_df, period=14)
            rsi_value = rsi.iloc[-1] if not rsi.empty and not np.isnan(rsi.iloc[-1]) else 0.0
            if rsi.empty or np.isnan(rsi_value):
                logger_main.info(f"Failed to calculate RSI for {symbol}")
            await redis_client.set_json(rsi_cache_key, rsi_value, expire=300)

        # MACD
        macd_cache_key = f"indicator:macd:{symbol}:4h"
        cached_macd = await redis_client.get_json(macd_cache_key)
        if cached_macd is not None:
            macd_value = cached_macd['macd']
            macd_signal_value = cached_macd['signal']
        else:
            close_df = pd.DataFrame({'close': ohlcv['close']})
            macd_df = calculate_macd(close_df, fast_period=12, slow_period=26, signal_period=9)
            macd_value = macd_df['macd'].iloc[-1] if not macd_df.empty and 'macd' in macd_df and not np.isnan(macd_df['macd'].iloc[-1]) else 0.0
            macd_signal_value = macd_df['signal'].iloc[-1] if not macd_df.empty and 'signal' in macd_df and not np.isnan(macd_df['signal'].iloc[-1]) else 0.0
            if macd_df.empty or np.isnan(macd_value) or np.isnan(macd_signal_value):
                logger_main.info(f"Failed to calculate MACD for {symbol}")
            await redis_client.set_json(macd_cache_key, {'macd': macd_value, 'signal': macd_signal_value}, expire=300)

        # Generate signal
        signal = 0
        if (latest_short_ma > latest_long_ma and
            latest_close > latest_short_ma and
            rsi_value < rsi_sell and
            macd_value > macd_signal_value and
            volatility < volatility_threshold):
            signal = 1  # Buy
        elif (latest_short_ma < latest_long_ma and
              latest_close < latest_short_ma and
              rsi_value > rsi_buy and
              macd_value < macd_signal_value and
              volatility < volatility_threshold):
            signal = -1  # Sell

        if success_prob is not None:
            if signal == 1 and success_prob < 0.5:
                signal = 0
            elif signal == -1 and success_prob < 0.5:
                signal = 0

        metrics = {
            'atr': atr_value,
            'short_ma': latest_short_ma,
            'long_ma': latest_long_ma,
            'rsi': rsi_value,
            'macd': macd_value,
            'macd_signal': macd_signal_value
        }
        return signal, metrics
    except Exception as e:
        logger_main.error(f"Error generating signal for {symbol}: {str(e)}")
        return 0, {'atr': 0.0, 'short_ma': 0.0, 'long_ma': 0.0, 'rsi': 0.0, 'macd': 0.0, 'macd_signal': 0.0}

__all__ = ['calculate_indicators_and_signal']
