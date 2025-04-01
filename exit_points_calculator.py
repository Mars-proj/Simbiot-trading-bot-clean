from logging_setup import logger_main

def calculate_exit_points(symbol, price, stop_loss_percent=0.05, take_profit_percent=0.1):
    """Calculates stop-loss and take-profit levels based on the current price."""
    try:
        if price <= 0:
            logger_main.error(f"Invalid price for {symbol}: {price}")
            return None, None
        if stop_loss_percent <= 0 or take_profit_percent <= 0:
            logger_main.error(f"Invalid stop_loss_percent ({stop_loss_percent}) or take_profit_percent ({take_profit_percent}) for {symbol}")
            return None, None

        stop_loss = price * (1 - stop_loss_percent)
        take_profit = price * (1 + take_profit_percent)
        logger_main.info(f"Calculated exit points for {symbol}: stop_loss={stop_loss}, take_profit={take_profit}")
        return stop_loss, take_profit
    except Exception as e:
        logger_main.error(f"Error calculating exit points for {symbol}: {e}")
        return None, None

__all__ = ['calculate_exit_points']
