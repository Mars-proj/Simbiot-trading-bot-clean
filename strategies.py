import pandas as pd
from logging_setup import logger_main
from ohlcv_fetcher import fetch_ohlcv

class TradingStrategy:
    """Manages trading strategies."""
    def __init__(self, name):
        self.name = name

    async def calculate_support_resistance(self, exchange_id, symbol, period=20):
        """Calculates support and resistance levels with configurable period."""
        try:
            ohlcv = await fetch_ohlcv(exchange_id, symbol, timeframe='1h', limit=period*2)
            if ohlcv is None or len(ohlcv) == 0:
                logger_main.error(f"Failed to fetch OHLCV data for {symbol} on {exchange_id}")
                return None, None

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            if 'high' not in df or 'low' not in df:
                raise ValueError("Data must contain 'high' and 'low' columns")
            support = df['low'].rolling(window=period).min()
            resistance = df['high'].rolling(window=period).max()
            logger_main.info(f"Calculated support and resistance for {self.name} on {symbol} with period {period}")
            return support.iloc[-1], resistance.iloc[-1]
        except Exception as e:
            logger_main.error(f"Error calculating support and resistance: {e}")
            return None, None

    async def recommend_strategy(self, exchange_id, symbol, period=100, short_ma=20, long_ma=50):
        """Recommends a trading strategy based on market trends using moving averages."""
        try:
            ohlcv = await fetch_ohlcv(exchange_id, symbol, timeframe='1h', limit=period)
            if ohlcv is None or len(ohlcv) == 0:
                logger_main.error(f"Failed to fetch OHLCV data for {symbol} on {exchange_id}")
                return None

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            if 'close' not in df:
                raise ValueError("Market data must contain 'close' column")

            # Calculate short and long moving averages
            df['short_ma'] = df['close'].rolling(window=short_ma).mean()
            df['long_ma'] = df['close'].rolling(window=long_ma).mean()

            # Determine trend
            latest_short_ma = df['short_ma'].iloc[-1]
            latest_long_ma = df['long_ma'].iloc[-1]
            latest_price = df['close'].iloc[-1]

            if latest_short_ma > latest_long_ma and latest_price > latest_short_ma:
                strategy = "trend_following"  # Uptrend
            elif latest_short_ma < latest_long_ma and latest_price < latest_short_ma:
                strategy = "mean_reversion"  # Downtrend
            else:
                strategy = "support_resistance"  # Sideways

            logger_main.info(f"Recommended strategy for {symbol}: {strategy} (short_ma={latest_short_ma}, long_ma={latest_long_ma}, price={latest_price})")
            return strategy
        except Exception as e:
            logger_main.error(f"Error recommending strategy: {e}")
            return None

__all__ = ['TradingStrategy']
