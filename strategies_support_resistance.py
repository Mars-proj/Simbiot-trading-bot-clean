import pandas as pd
import numpy as np
import pandas_ta as ta
from utils import logger_main
from global_objects import redis_client, global_trade_pool
from momentum_indicators import calculate_rsi
from trend_indicators import calculate_macd

async def generate_support_resistance_signals(df, market_conditions=None, success_prob=None, user_id=None):
    """
    Generates signals based on RSI, with optional additional conditions.
    Arguments:
    - df: DataFrame with OHLCV data.
    - market_conditions: Dictionary with market conditions (avg_volatility, avg_drop, trend).
    - success_prob: Success probability of the trade (0 to 1), can be None.
    - user_id: User ID to fetch recent trade success (optional).
    Returns:
    - signal: 1 (buy), -1 (sell), 0 (no signal).
    """
    logger_main.debug("Generating signals for support and resistance strategy")
    try:
        # Check if enough data is available
        if len(df) < 50:
            logger_main.warning("Insufficient data for generating support and resistance signals")
            return 0
        # Calculate volatility for adaptive thresholds
        volatility_cache_key = f"indicator:volatility:{df.index[-1]}"
        cached_volatility = await redis_client.get_json(volatility_cache_key)
        if cached_volatility is not None:
            volatility = cached_volatility
            logger_main.debug(f"Using cached volatility: {volatility:.4f}")
        else:
            df['returns'] = df['close'].pct_change()
            volatility = df['returns'].rolling(window=20).std().iloc[-1] * np.sqrt(252) if not df['returns'].empty else 0
            await redis_client.set_json(volatility_cache_key, volatility, expire=300)  # Cache for 5 minutes
        logger_main.debug(f"Current volatility: {volatility:.4f}")
        # Calculate RSI
        rsi_cache_key = f"indicator:rsi:{df.index[-1]}"
        cached_rsi = await redis_client.get_json(rsi_cache_key)
        if cached_rsi is not None:
            current_rsi = cached_rsi
            logger_main.debug(f"Using cached RSI: {current_rsi:.2f}")
        else:
            df['rsi'] = ta.rsi(df['close'], length=14)
            current_rsi = df['rsi'].iloc[-1]
            if pd.isna(current_rsi):
                logger_main.info("Failed to calculate RSI")
                current_rsi = 0.0
            await redis_client.set_json(rsi_cache_key, current_rsi, expire=300)
        logger_main.debug(f"Current RSI: {current_rsi:.2f}")
        # Calculate moving averages for trend confirmation
        short_window = 10 if volatility < 0.1 else 5
        long_window = 30 if volatility < 0.1 else 15
        short_ma_cache_key = f"indicator:short_ma:{df.index[-1]}:{short_window}"
        long_ma_cache_key = f"indicator:long_ma:{df.index[-1]}:{long_window}"
        cached_short_ma = await redis_client.get_json(short_ma_cache_key)
        cached_long_ma = await redis_client.get_json(long_ma_cache_key)
        if cached_short_ma is not None and cached_long_ma is not None:
            short_ma = cached_short_ma
            long_ma = cached_long_ma
            logger_main.debug(f"Using cached MAs: short_ma={short_ma:.4f}, long_ma={long_ma:.4f}")
        else:
            df['short_ma'] = df['close'].rolling(window=short_window, min_periods=1).mean()
            df['long_ma'] = df['close'].rolling(window=long_window, min_periods=1).mean()
            short_ma = df['short_ma'].iloc[-1]
            long_ma = df['long_ma'].iloc[-1]
            if pd.isna(short_ma) or pd.isna(long_ma):
                logger_main.info(f"NaN in moving averages: short_ma={short_ma}, long_ma={long_ma}")
                short_ma = long_ma = 0.0
            await redis_client.set_json(short_ma_cache_key, short_ma, expire=300)
            await redis_client.set_json(long_ma_cache_key, long_ma, expire=300)
        # Calculate MACD for trend confirmation
        macd_cache_key = f"indicator:macd:{df.index[-1]}"
        cached_macd = await redis_client.get_json(macd_cache_key)
        if cached_macd is not None:
            macd = cached_macd['macd']
            macd_signal = cached_macd['signal']
            logger_main.debug(f"Using cached MACD: macd={macd:.4f}, signal={macd_signal:.4f}")
        else:
            close_df = pd.DataFrame({'close': df['close']})
            macd_df = calculate_macd(close_df, fast_period=12, slow_period=26, signal_period=9)
            macd = macd_df['macd'].iloc[-1] if not macd_df.empty and 'macd' in macd_df and not np.isnan(macd_df['macd'].iloc[-1]) else 0.0
            macd_signal = macd_df['signal'].iloc[-1] if not macd_df.empty and 'signal' in macd_df and not np.isnan(macd_df['signal'].iloc[-1]) else 0.0
            if macd_df.empty or np.isnan(macd) or np.isnan(macd_signal):
                logger_main.info("Failed to calculate MACD")
                macd = macd_signal = 0.0
            await redis_client.set_json(macd_cache_key, {'macd': macd, 'signal': macd_signal}, expire=300)
        # Dynamic RSI thresholds
        avg_volatility = market_conditions.get('avg_volatility', 0) if market_conditions else 0
        base_rsi_buy = 40.0  # Lowered from 45 to make signals more frequent
        base_rsi_sell = 60.0  # Lowered from 55 to make signals more frequent
        volatility_factor = 1.0 + (avg_volatility / 2)  # Increase sensitivity with volatility
        success_factor = 1.0
        if user_id:
            recent_trades = await global_trade_pool.get_recent_trades(limit=10, user_id=user_id)
            if recent_trades:
                successful_trades = sum(1 for trade in recent_trades if trade.get('pnl', 0) > 0)
                success_rate = successful_trades / len(recent_trades)
                success_factor = 0.5 + success_rate  # Range: 0.5 to 1.5
                logger_main.info(f"Recent trade success rate for {user_id}: {success_rate:.2f}, success_factor: {success_factor:.2f}")
        # Adjust RSI thresholds
        rsi_buy = base_rsi_buy * (1 / volatility_factor) * success_factor
        rsi_sell = base_rsi_sell * (1 / volatility_factor) * (2 - success_factor)
        rsi_buy = max(20, min(40, rsi_buy))  # Keep within reasonable bounds
        rsi_sell = max(60, min(80, rsi_sell))
        # Adjust based on success_prob
        if success_prob is not None:
            if success_prob > 0.7:  # High success probability
                rsi_buy *= 0.9  # More aggressive
                rsi_sell *= 1.1
                logger_main.debug(f"High success probability ({success_prob:.2f}), adjusted RSI thresholds: buy={rsi_buy:.2f}, sell={rsi_sell:.2f}")
            elif success_prob < 0.3:  # Low success probability
                rsi_buy *= 1.1  # More conservative
                rsi_sell *= 0.9
                logger_main.debug(f"Low success probability ({success_prob:.2f}), adjusted RSI thresholds: buy={rsi_buy:.2f}, sell={rsi_sell:.2f}")
        logger_main.debug(f"Dynamic RSI thresholds: buy at RSI < {rsi_buy:.2f}, sell at RSI > {rsi_sell:.2f}")
        # Generate signals
        signal = 0
        # Buy condition: RSI < rsi_buy, optionally confirmed by trend
        if current_rsi < rsi_buy:
            if market_conditions and market_conditions.get('trend') == 'down':
                logger_main.debug(f"Buy signal suppressed due to downtrend: RSI={current_rsi:.2f}")
            elif short_ma > long_ma and macd > macd_signal:
                signal = 1  # Buy
                logger_main.debug(f"Support signal: buy (RSI={current_rsi:.2f} < {rsi_buy:.2f}, short_ma={short_ma:.4f} > long_ma={long_ma:.4f}, MACD={macd:.4f} > signal={macd_signal:.4f})")
            else:
                signal = 1  # Buy (RSI only)
                logger_main.debug(f"Support signal: buy (RSI={current_rsi:.2f} < {rsi_buy:.2f})")
        # Sell condition: RSI > rsi_sell, optionally confirmed by trend
        elif current_rsi > rsi_sell:
            if market_conditions and market_conditions.get('trend') == 'up':
                logger_main.debug(f"Sell signal suppressed due to uptrend: RSI={current_rsi:.2f}")
            elif short_ma < long_ma and macd < macd_signal:
                signal = -1  # Sell
                logger_main.debug(f"Resistance signal: sell (RSI={current_rsi:.2f} > {rsi_sell:.2f}, short_ma={short_ma:.4f} < long_ma={long_ma:.4f}, MACD={macd:.4f} < signal={macd_signal:.4f})")
            else:
                signal = -1  # Sell (RSI only)
                logger_main.debug(f"Resistance signal: sell (RSI={current_rsi:.2f} > {rsi_sell:.2f})")
        return signal
    except Exception as e:
        logger_main.error(f"Error generating support/resistance signals: {str(e)}")
        return 0
