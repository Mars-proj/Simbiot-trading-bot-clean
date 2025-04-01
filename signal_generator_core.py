from logging_setup import logger_main

def generate_signal(rsi, overbought_threshold=70, oversold_threshold=30):
    """Generates a trading signal based on RSI."""
    try:
        if rsi is None:
            logger_main.error("RSI value is None")
            return None
        if overbought_threshold <= oversold_threshold:
            logger_main.error(f"Invalid thresholds: overbought={overbought_threshold}, oversold={oversold_threshold}")
            return None

        if rsi > overbought_threshold:
            signal = 'sell'
        elif rsi < oversold_threshold:
            signal = 'buy'
        else:
            signal = None

        logger_main.info(f"Generated signal based on RSI={rsi}: {signal}")
        return signal
    except Exception as e:
        logger_main.error(f"Error generating signal: {e}")
        return None

__all__ = ['generate_signal']
