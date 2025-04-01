from logging_setup import logger_main

def calculate_fee(trade_value, fee_rate=0.001):
    """Calculates the fee for a trade based on the trade value and fee rate."""
    try:
        if trade_value < 0:
            logger_main.error(f"Invalid trade value: {trade_value}")
            return None
        if fee_rate < 0:
            logger_main.error(f"Invalid fee rate: {fee_rate}")
            return None

        fee = trade_value * fee_rate
        logger_main.info(f"Calculated fee for trade value {trade_value}: fee={fee}")
        return fee
    except Exception as e:
        logger_main.error(f"Error calculating fee: {e}")
        return None

__all__ = ['calculate_fee']
