from logging_setup import logger_main

def calculate_deposit(symbol: str, amount: float, margin_multiplier=2.0) -> float:
    """Calculates the required deposit for a trade with configurable margin multiplier."""
    try:
        required_deposit = amount * margin_multiplier
        logger_main.info(f"Calculated deposit for {symbol}: amount={amount}, margin_multiplier={margin_multiplier}, required_deposit={required_deposit}")
        return required_deposit
    except Exception as e:
        logger_main.error(f"Error calculating deposit for {symbol}: {e}")
        return None

__all__ = ['calculate_deposit']
