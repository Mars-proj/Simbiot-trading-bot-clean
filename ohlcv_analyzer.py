import pandas as pd
from logging_setup import logger_main

def analyze_ohlcv(data):
    """Analyzes OHLCV data for patterns or anomalies."""
    try:
        if not isinstance(data, pd.DataFrame):
            logger_main.error(f"Data must be a pandas DataFrame, got {type(data)}")
            return None
        if data.empty:
            logger_main.error("OHLCV data is empty")
            return None
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in data.columns:
                logger_main.error(f"Missing required column: {col}")
                return None

        # Basic statistics
        analysis = {
            'average_price': data['close'].mean(),
            'max_volume': data['volume'].max(),
            'price_range': data['high'].max() - data['low'].min(),
            'patterns': []
        }

        # Detect candlestick patterns (e.g., Hammer and Bearish Engulfing)
        for i in range(1, len(data)):
            prev_candle = data.iloc[i-1]
            curr_candle = data.iloc[i]

            # Hammer pattern (bullish reversal)
            body = abs(curr_candle['close'] - curr_candle['open'])
            lower_shadow = curr_candle['low'] - min(curr_candle['open'], curr_candle['close'])
            upper_shadow = max(curr_candle['open'], curr_candle['close']) - curr_candle['high']
            if lower_shadow > 2 * body and upper_shadow < body and curr_candle['close'] > curr_candle['open']:
                analysis['patterns'].append({'type': 'hammer', 'timestamp': curr_candle['timestamp']})

            # Bearish Engulfing pattern
            if (prev_candle['close'] > prev_candle['open'] and  # Previous candle is bullish
                curr_candle['open'] > prev_candle['close'] and  # Current candle opens above previous close
                curr_candle['close'] < prev_candle['open'] and  # Current candle closes below previous open
                curr_candle['close'] < curr_candle['open']):     # Current candle is bearish
                analysis['patterns'].append({'type': 'bearish_engulfing', 'timestamp': curr_candle['timestamp']})

        logger_main.info(f"OHLCV analysis: {analysis}")
        return analysis
    except Exception as e:
        logger_main.error(f"Error analyzing OHLCV data: {e}")
        return None

__all__ = ['analyze_ohlcv']
