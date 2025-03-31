from logging_setup import logger_main
from global_objects import SUPPORTED_SYMBOLS

def generate_base_signal(price: float, avg_price: float, overbought_threshold=1.05, oversold_threshold=0.95) -> str:
    """Generates a basic trading signal based on price comparison with configurable thresholds."""
    try:
        if price > avg_price * overbought_threshold:  # Above average by threshold
            signal = "sell"
        elif price < avg_price * oversold_threshold:  # Below average by threshold
            signal = "buy"
        else:
            signal = None  # Neutral
        logger_main.info(f"Generated base signal: price={price}, avg_price={avg_price}, signal={signal}")
        return signal
    except Exception as e:
        logger_main.error(f"Error generating base signal: {e}")
        return None

__all__ = ['generate_base_signal']
