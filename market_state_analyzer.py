# market_state_analyzer.py
import logging
import numpy as np
import pandas as pd

logger = logging.getLogger("main")

async def calculate_adx(exchange, symbol, timeframe='4h', period=14, limit=100):
    """Calculates ADX (Average Directional Index) to determine trend strength."""
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        if not ohlcv or len(ohlcv) < period + 1:
            logger.warning(f"Insufficient data to calculate ADX for {symbol}")
            return 0

        highs = [candle[2] for candle in ohlcv]
        lows = [candle[3] for candle in ohlcv]
        closes = [candle[4] for candle in ohlcv]

        df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes})
        df['plus_dm'] = np.where((df['high'] - df['high'].shift(1)) > (df['low'].shift(1) - df['low']),
                                np.maximum(df['high'] - df['high'].shift(1), 0), 0)
        df['minus_dm'] = np.where((df['low'].shift(1) - df['low']) > (df['high'] - df['high'].shift(1)),
                                 np.maximum(df['low'].shift(1) - df['low'], 0), 0)

        df['tr'] = np.maximum(df['high'] - df['low'],
                             np.maximum(abs(df['high'] - df['close'].shift(1)),
                                       abs(df['low'] - df['close'].shift(1))))
        df['plus_di'] = 100 * df['plus_dm'].rolling(window=period).mean() / df['tr'].rolling(window=period).mean()
        df['minus_di'] = 100 * df['minus_dm'].rolling(window=period).mean() / df['tr'].rolling(window=period).mean()
        df['dx'] = 100 * abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])
        df['adx'] = df['dx'].rolling(window=period).mean()

        adx = df['adx'].iloc[-1]
        return adx if not np.isnan(adx) else 0
    except Exception as e:
        logger.error(f"Failed to calculate ADX for {symbol}: {type(e).__name__}: {str(e)}")
        return 0

async def calculate_bollinger_width(exchange, symbol, timeframe='4h', period=20, limit=100):
    """Calculates Bollinger Band Width to determine if the market is sideways."""
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        if not ohlcv or len(ohlcv) < period:
            logger.warning(f"Insufficient data to calculate Bollinger Bands for {symbol}")
            return 0

        closes = [candle[4] for candle in ohlcv]
        df = pd.Series(closes)

        sma = df.rolling(window=period).mean()
        std = df.rolling(window=period).std()
        upper_band = sma + 2 * std
        lower_band = sma - 2 * std
        bb_width = (upper_band - lower_band) / sma

        return bb_width.iloc[-1] if not np.isnan(bb_width.iloc[-1]) else 0
    except Exception as e:
        logger.error(f"Failed to calculate Bollinger Band Width for {symbol}: {type(e).__name__}: {str(e)}")
        return 0

async def calculate_atr(exchange, symbol, timeframe='4h', period=14, limit=100):
    """Calculates ATR (Average True Range) to measure volatility."""
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        if not ohlcv or len(ohlcv) < period + 1:
            logger.warning(f"Insufficient data to calculate ATR for {symbol}")
            return 0

        highs = [candle[2] for candle in ohlcv]
        lows = [candle[3] for candle in ohlcv]
        closes = [candle[4] for candle in ohlcv]

        df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes})
        df['tr'] = np.maximum(df['high'] - df['low'],
                             np.maximum(abs(df['high'] - df['close'].shift(1)),
                                       abs(df['low'] - df['close'].shift(1))))
        df['atr'] = df['tr'].rolling(window=period).mean()

        atr = df['atr'].iloc[-1]
        return atr if not np.isnan(atr) else 0
    except Exception as e:
        logger.error(f"Failed to calculate ATR for {symbol}: {type(e).__name__}: {str(e)}")
        return 0

async def analyze_market_state(exchange_pool, timeframe):
    """
    Analyzes the market state using the exchange pool.
    Returns a dictionary with trend, volatility, and market type.
    """
    try:
        markets = exchange_pool.get_markets()
        if not markets:
            logger.error("No markets available for analysis")
            return {"trend": "neutral", "volatility": 0.01, "market_type": "sideways"}

        # Use BTC/USDT as a reference symbol for market state
        reference_symbol = "BTC/USDT"
        ohlcv = await exchange_pool.exchange.fetch_ohlcv(reference_symbol, timeframe, limit=100)
        if not ohlcv or len(ohlcv) < 50:
            logger.warning(f"Insufficient data for {reference_symbol}")
            return {"trend": "neutral", "volatility": 0.01, "market_type": "sideways"}

        # Calculate trend (simple moving average comparison)
        closes = [candle[4] for candle in ohlcv]
        short_ma = np.mean(closes[-10:])
        long_ma = np.mean(closes[-50:])
        if short_ma > long_ma:
            trend = "bullish"
        elif short_ma < long_ma:
            trend = "bearish"
        else:
            trend = "neutral"

        # Calculate volatility (standard deviation of returns)
        returns = np.diff(closes) / closes[:-1]
        volatility = np.std(returns) * np.sqrt(24 * 365)  # Annualized volatility
        volatility = volatility if not np.isnan(volatility) else 0.01

        # Determine market type
        adx = await calculate_adx(exchange_pool.exchange, reference_symbol, timeframe)
        bb_width = await calculate_bollinger_width(exchange_pool.exchange, reference_symbol, timeframe)
        atr = await calculate_atr(exchange_pool.exchange, reference_symbol, timeframe)

        # Calculate average ATR for comparison
        atr_values = []
        for i in range(-5, 0):
            sub_ohlcv = ohlcv[i-14:i] if i + 14 <= 0 else ohlcv[-14:]
            if len(sub_ohlcv) >= 14:
                sub_atr = await calculate_atr(exchange_pool.exchange, reference_symbol, timeframe, limit=len(sub_ohlcv))
                atr_values.append(sub_atr)
        avg_atr = np.mean(atr_values) if atr_values else atr

        # Determine market type
        if adx > 25:  # Strong trend
            market_type = "trending"
        elif bb_width < 0.05:  # Narrow Bollinger Bands indicate sideways market
            market_type = "sideways"
        elif atr > avg_atr * 1.5:  # High volatility
            market_type = "volatile"
        else:
            market_type = "sideways"

        logger.info(f"Market state: trend={trend}, volatility={volatility}, market_type={market_type}, adx={adx}, bb_width={bb_width}, atr={atr}, avg_atr={avg_atr}")
        return {"trend": trend, "volatility": volatility, "market_type": market_type}
    except Exception as e:
        logger.error(f"Failed to analyze market state: {type(e).__name__}: {str(e)}")
        return {"trend": "neutral", "volatility": 0.01, "market_type": "sideways"}
