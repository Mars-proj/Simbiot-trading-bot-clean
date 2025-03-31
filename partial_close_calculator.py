from logging_setup import logger_main
from config_keys import MIN_TRADE_AMOUNT

def calculate_partial_close(position_size, close_percentage=0.5, min_close_amount=MIN_TRADE_AMOUNT):
    """Calculates the amount to close for a partial position close."""
    try:
        if position_size <= 0:
            logger_main.error(f"Position size must be positive, got {position_size}")
            return None
        if not 0 < close_percentage <= 1:
            logger_main.error(f"Close percentage must be between 0 and 1, got {close_percentage}")
            return None

        close_amount = position_size * close_percentage
        if close_amount < min_close_amount:
            logger_main.error(f"Close amount {close_amount} is below minimum {min_close_amount}")
            return None

        logger_main.info(f"Calculated partial close: position_size={position_size}, close_percentage={close_percentage}, close_amount={close_amount}")
        return close_amount
    except Exception as e:
        logger_main.error(f"Error calculating partial close: {e}")
        return None

__all__ = ['calculate_partial_close']
