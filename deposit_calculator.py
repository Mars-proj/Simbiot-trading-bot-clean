from logging_setup import logger_main
import os

def calculate_deposit(symbol, amount, margin_multiplier=2.0):
    """Calculates the required deposit for a trade."""
    try:
        if amount <= 0:
            logger_main.error(f"Invalid amount for {symbol}: {amount}")
            return None

        # Minimum deposit requirement (example value, can be made configurable)
        min_deposit = float(os.getenv("MIN_DEPOSIT", 10.0))  # e.g., 10 USDT minimum

        required_deposit = amount * margin_multiplier
        if required_deposit < min_deposit:
            logger_main.warning(f"Required deposit {required_deposit} for {symbol} is below minimum {min_deposit}, adjusting")
            required_deposit = min_deposit

        logger_main.info(f"Calculated required deposit for {symbol}: {required_deposit}")
        return required_deposit
    except Exception as e:
        logger_main.error(f"Error calculating deposit for {symbol}: {e}")
        return None

__all__ = ['calculate_deposit']
