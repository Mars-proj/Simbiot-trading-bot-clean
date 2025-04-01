from logging_setup import logger_main

def calculate_deposit(symbol, amount, margin_multiplier=2.0):
    """Calculates the required deposit for a trade."""
    try:
        if amount <= 0:
            logger_main.error(f"Invalid amount for {symbol}: {amount}")
            return None
        if margin_multiplier <= 0:
            logger_main.error(f"Invalid margin multiplier for {symbol}: {margin_multiplier}")
            return None

        required_deposit = amount * margin_multiplier
        min_deposit = 10.0  # Example minimum deposit in USDT
        if required_deposit < min_deposit:
            logger_main.warning(f"Required deposit {required_deposit} for {symbol} is below minimum {min_deposit}, adjusting")
            required_deposit = min_deposit

        logger_main.info(f"Calculated required deposit for {symbol}: {required_deposit}")
        return required_deposit
    except Exception as e:
        logger_main.error(f"Error calculating deposit for {symbol}: {e}")
        return None

__all__ = ['calculate_deposit']
