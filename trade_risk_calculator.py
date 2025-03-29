import asyncio
from logging_setup import logger_main
from utils import log_exception
from global_objects import global_trade_pool

class TradeRiskCalculator:
    def __init__(self, risk_manager):
        self.risk_manager = risk_manager
        self.blacklist = set()

    async def calculate_trade_percentage(self, market_conditions=None, user_id=None):
        """Calculates the percentage of deposit to use for a trade, dynamically"""
        logger_main.info("Calculating deposit percentage for trade with risk management")
        try:
            drawdown = self.risk_manager.get_current_drawdown()
            logger_main.info(f"Current drawdown: {drawdown:.2f}%")
            # Base percentage starts at 10%
            base_percentage = 0.1
            # Adjust based on drawdown (reduce risk if drawdown is high)
            drawdown_factor = max(0.1, 1.0 - (drawdown / self.risk_manager.max_drawdown))
            # Adjust based on market conditions
            volatility_factor = 1.0
            if market_conditions:
                volatility = market_conditions.get('volatility', 0)
                logger_main.info(f"Market volatility: {volatility:.4f}")
                # Reduce risk during high volatility
                if volatility > 0.5:
                    volatility_factor = 0.5
                elif volatility < 0.2:
                    volatility_factor = 1.5  # Increase risk during low volatility
            # Adjust based on recent trade success
            success_factor = 1.0
            if user_id:
                recent_trades = await global_trade_pool.get_recent_trades(limit=10, user_id=user_id)
                if recent_trades:
                    successful_trades = sum(1 for trade in recent_trades if trade.get('pnl', 0) > 0)
                    success_rate = successful_trades / len(recent_trades)
                    logger_main.info(f"Recent trade success rate for {user_id}: {success_rate:.2f}")
                    success_factor = 0.5 + success_rate  # Range: 0.5 to 1.5
            # Combine factors
            trade_percentage = base_percentage * drawdown_factor * volatility_factor * success_factor
            # Ensure trade_percentage is within reasonable bounds
            trade_percentage = max(0.01, min(0.3, trade_percentage))
            logger_main.info(f"Calculated trade percentage: {trade_percentage:.4f} (drawdown_factor={drawdown_factor:.2f}, volatility_factor={volatility_factor:.2f}, success_factor={success_factor:.2f})")
            return trade_percentage
        except Exception as e:
            logger_main.error(f"Error calculating deposit percentage: {str(e)}")
            log_exception(f"Error calculating percentage: {str(e)}", e)
            return 0.1

    async def check_drawdown(self, exchange, user_id, deposit_manager):
        """Checks if the current drawdown is within acceptable limits"""
        logger_main.info(f"Checking drawdown for user {user_id}")
        try:
            total_deposit = await deposit_manager.calculate_total_deposit(exchange, user_id)
            current_drawdown = self.risk_manager.get_current_drawdown()
            max_drawdown = self.risk_manager.max_drawdown
            logger_main.info(f"Current drawdown: {current_drawdown:.2f}%, max allowed: {max_drawdown:.2f}%")
            return current_drawdown <= max_drawdown
        except Exception as e:
            logger_main.error(f"Error checking drawdown for {user_id}: {str(e)}")
            log_exception(f"Error checking drawdown: {str(e)}", e)
            return False

    def is_symbol_in_blacklist(self, symbol):
        """Checks if a symbol is in the blacklist"""
        logger_main.info(f"Checking blacklist for symbol {symbol}: {'in blacklist' if symbol in self.blacklist else 'not in blacklist'}")
        return symbol in self.blacklist

__all__ = ['TradeRiskCalculator']
