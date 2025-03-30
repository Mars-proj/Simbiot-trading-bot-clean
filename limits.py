from logging_setup import logger_main
from config_keys import MAX_OPEN_TRADES, MIN_TRADE_AMOUNT, MAX_LEVERAGE

def check_limits(amount, leverage, open_trades):
    """Checks trading limits for amount, leverage, and number of open trades."""
    try:
        # Check amount
        if amount < MIN_TRADE_AMOUNT:
            logger_main.error(f"Amount {amount} is below minimum trade amount {MIN_TRADE_AMOUNT}")
            return False

        # Check leverage
        if leverage > MAX_LEVERAGE:
            logger_main.error(f"Leverage {leverage} exceeds maximum allowed leverage {MAX_LEVERAGE}")
            return False

        # Check number of open trades
        if len(open_trades) >= MAX_OPEN_TRADES:
            logger_main.error(f"Number of open trades {len(open_trades)} exceeds maximum allowed {MAX_OPEN_TRADES}")
            return False

        logger_main.info(f"Limits check passed: amount={amount}, leverage={leverage}, open_trades={len(open_trades)}")
        return True
    except Exception as e:
        logger_main.error(f"Error checking limits: {e}")
        return False

__all__ = ['check_limits']
