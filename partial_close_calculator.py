from logging_setup import logger_main
from config_keys import MIN_TRADE_AMOUNT

def calculate_partial_close(position_size, close_percentage=0.5):
    """Calculates the amount to close for a partial position close."""
    try:
        if position_size <= 0:
            logger_main.error(f"Invalid position size: {position_size}")
            return None
        if close_percentage <= 0 or close_percentage > 1:
            logger_main.error(f"Invalid close percentage: {close_percentage}")
            return None

        close_amount = position_size * close_percentage
        if close_amount < MIN_TRADE_AMOUNT:
            logger_main.warning(f"Close amount {close_amount} is below minimum trade amount {MIN_TRADE_AMOUNT}, adjusting")
            close_amount = MIN_TRADE_AMOUNT

        logger_main.info(f"Calculated partial close amount: {close_amount} for position size {position_size} with close percentage {close_percentage}")
        return close_amount
    except Exception as e:
        logger_main.error(f"Error calculating partial close: {e}")
        return None

__all__ = ['calculate_partial_close']
