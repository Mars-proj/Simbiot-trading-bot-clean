from logging_setup import logger_main

def calculate_risk(amount, leverage, stop_loss, price, available_balance, max_risk_percentage=0.02):
    """Calculates the risk of a trade."""
    try:
        if amount <= 0 or leverage <= 0 or price <= 0 or available_balance <= 0:
            logger_main.error(f"Invalid inputs for risk calculation: amount={amount}, leverage={leverage}, price={price}, available_balance={available_balance}")
            return None
        if stop_loss <= 0 or stop_loss >= price:
            logger_main.error(f"Invalid stop loss: {stop_loss}, must be positive and less than price {price}")
            return None
        if max_risk_percentage <= 0 or max_risk_percentage > 1:
            logger_main.error(f"Invalid max risk percentage: {max_risk_percentage}")
            return None

        # Calculate potential loss
        position_value = amount * price * leverage
        loss_per_unit = price - stop_loss
        total_loss = loss_per_unit * amount * leverage

        # Calculate risk as a percentage of available balance
        risk_percentage = total_loss / available_balance
        if risk_percentage > max_risk_percentage:
            logger_main.error(f"Risk {risk_percentage:.2%} exceeds maximum allowed risk {max_risk_percentage:.2%}")
            return None

        logger_main.info(f"Calculated risk: {risk_percentage:.2%} (total loss={total_loss}, position_value={position_value})")
        return risk_percentage
    except Exception as e:
        logger_main.error(f"Error calculating risk: {e}")
        return None

__all__ = ['calculate_risk']
