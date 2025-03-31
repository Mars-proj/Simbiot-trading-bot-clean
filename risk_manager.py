from logging_setup import logger_main

def calculate_risk(amount, leverage, stop_loss_price, entry_price, balance, max_risk_percentage=0.02):
    """Calculates the risk of a trade and checks if it exceeds the maximum allowed risk."""
    try:
        if amount <= 0 or leverage <= 0:
            logger_main.error(f"Amount and leverage must be positive: amount={amount}, leverage={leverage}")
            return None
        if stop_loss_price <= 0 or entry_price <= 0:
            logger_main.error(f"Stop-loss and entry price must be positive: stop_loss_price={stop_loss_price}, entry_price={entry_price}")
            return None
        if balance <= 0:
            logger_main.error(f"Balance must be positive, got {balance}")
            return None
        if not 0 < max_risk_percentage <= 1:
            logger_main.error(f"Max risk percentage must be between 0 and 1, got {max_risk_percentage}")
            return None

        position_size = amount * leverage
        risk_per_unit = abs(entry_price - stop_loss_price)
        total_risk = position_size * risk_per_unit
        max_allowed_risk = balance * max_risk_percentage

        if total_risk > max_allowed_risk:
            logger_main.error(f"Total risk {total_risk} exceeds maximum allowed risk {max_allowed_risk} ({max_risk_percentage*100}% of balance)")
            return None

        logger_main.info(f"Calculated risk: position_size={position_size}, risk_per_unit={risk_per_unit}, total_risk={total_risk}, max_allowed_risk={max_allowed_risk}")
        return total_risk
    except Exception as e:
        logger_main.error(f"Error calculating risk: {e}")
        return None

__all__ = ['calculate_risk']
