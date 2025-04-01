import pandas as pd
from logging_setup import logger_main

def analyze_ohlcv(data):
    """Analyzes OHLCV data for candlestick patterns and trends."""
    try:
        if not isinstance(data, pd.DataFrame):
            logger_main.error(f"Data must be a pandas DataFrame, got {type(data)}")
            return None
        if data.empty:
            logger_main.error("DataFrame is empty")
            return None
        required_columns = ['open', 'high', 'low', 'close']
        if not all(col in data.columns for col in required_columns):
            missing = [col for col in required_columns if col not in data.columns]
            logger_main.error(f"DataFrame missing required columns: {missing}")
            return None

        # Detect simple candlestick patterns (e.g., Doji, Hammer)
        patterns = []
        for i in range(1, len(data)):
            open_price = data['open'].iloc[i]
            high_price = data['high'].iloc[i]
            low_price = data['low'].iloc[i]
            close_price = data['close'].iloc[i]

            # Calculate body and shadow lengths
            body_length = abs(close_price - open_price)
            upper_shadow = high_price - max(open_price, close_price)
            lower_shadow = min(open_price, close_price) - low_price
            total_range = high_price - low_price

            # Doji pattern: very small body
            if total_range > 0 and body_length / total_range < 0.1:
                patterns.append({'index': i, 'pattern': 'Doji'})
            # Hammer pattern: small body, long lower shadow
            elif total_range > 0 and body_length / total_range < 0.3 and lower_shadow > 2 * body_length and upper_shadow < body_length:
                patterns.append({'index': i, 'pattern': 'Hammer'})

        # Analyze trend (simple moving average crossover)
        short_ma = data['close'].rolling(window=20).mean()
        long_ma = data['close'].rolling(window=50).mean()
        latest_short_ma = short_ma.iloc[-1]
        latest_long_ma = long_ma.iloc[-1]
        trend = 'bullish' if latest_short_ma > latest_long_ma else 'bearish' if latest_short_ma < latest_long_ma else 'neutral'

        analysis = {
            'patterns': patterns,
            'trend': trend,
            'latest_short_ma': latest_short_ma,
            'latest_long_ma': latest_long_ma
        }

        logger_main.info(f"OHLCV analysis completed: trend={trend}, patterns_detected={len(patterns)}")
        return analysis
    except Exception as e:
        logger_main.error(f"Error analyzing OHLCV data: {e}")
        return None

__all__ = ['analyze_ohlcv']
