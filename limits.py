from logging_setup import logger_main
from config_keys import MAX_OPEN_TRADES, MIN_TRADE_AMOUNT

def check_limits(amount, leverage, open_trades, max_open_trades=MAX_OPEN_TRADES, min_trade_amount=MIN_TRADE_AMOUNT, max_total_position=10000):
    """Checks if a trade complies with risk management limits."""
    try:
        if amount < min_trade_amount:
            logger_main.error(f"Trade amount {amount} is below minimum {min_trade_amount}")
            return False
        if len(open_trades) >= max_open_trades:
            logger_main.error(f"Maximum number of open trades ({max_open_trades}) reached")
            return False

        # Check total position size
        total_position = sum(trade['amount'] * trade['price'] for trade in open_trades if 'amount' in trade and 'price' in trade)
        new_position = amount * leverage
        if total_position + new_position > max_total_position:
            logger_main.error(f"Total position size {total_position + new_position} exceeds maximum {max_total_position}")
            return False

        logger_main.info("Trade limits check passed")
        return True
    except Exception as e:
        logger_main.error(f"Error checking trade limits: {e}")
        return False

__all__ = ['check_limits']
