import pandas as pd
from global_objects import global_trade_pool

class RiskManager:
    def __init__(self, max_drawdown=0.2, base_trade_percentage=0.1):
        """
        Initializes RiskManager.
        Arguments:
        - max_drawdown: Maximum allowed drawdown of the deposit (e.g., 0.2 = 20%).
        - base_trade_percentage: Base percentage of the deposit for a trade (e.g., 0.1 = 10%).
        """
        self.max_drawdown = max_drawdown  # Renamed base_max_drawdown to max_drawdown
        self.base_trade_percentage = base_trade_percentage
        self.initial_deposit = None
        self.current_deposit = None

    def initialize_logging(self):
        """Initializes logging for RiskManager"""
        from logging_setup import logger_main
        logger_main.info("RiskManager initialized")

    def set_initial_deposit(self, initial_deposit):
        """Sets the initial deposit"""
        from logging_setup import logger_main
        self.initial_deposit = initial_deposit
        self.current_deposit = initial_deposit
        logger_main.info(f"Initial deposit set: {self.initial_deposit} USDT")

    def update_deposit(self, current_deposit):
        """Updates the current deposit"""
        from logging_setup import logger_main
        self.current_deposit = current_deposit
        logger_main.info(f"Current deposit updated: {self.current_deposit} USDT")

    def get_current_drawdown(self):
        """Returns the current drawdown"""
        from logging_setup import logger_main
        if self.initial_deposit is None or self.current_deposit is None:
            logger_main.warning("Initial or current deposit not set, drawdown = 0")
            return 0.0
        if self.initial_deposit == 0:
            logger_main.warning("Initial deposit is 0, drawdown cannot be calculated, returning 0")
            return 0.0
        drawdown = (self.initial_deposit - self.current_deposit) / self.initial_deposit
        return drawdown

    async def calculate_trade_percentage(self, market_conditions=None):
        """
        Calculates the percentage of the deposit to use for a trade, considering risk.
        Arguments:
        - market_conditions: Dictionary with market conditions (avg_volatility, avg_drop).
        Returns:
        - trade_percentage: Percentage of the deposit to use for the trade.
        - can_trade: Whether trading is allowed (True/False).
        """
        from logging_setup import logger_main
        logger_main.info("Calculating deposit percentage for trade with risk management")
        try:
            # Check if initial deposit is set
            if self.initial_deposit is None or self.current_deposit is None:
                logger_main.warning("Initial or current deposit not set, using base percentage")
                return self.base_trade_percentage, True
            # Calculate drawdown
            drawdown = self.get_current_drawdown()
            logger_main.info(f"Current drawdown: {drawdown:.2%}")
            # Adjust max_drawdown based on volatility
            max_drawdown = self.max_drawdown
            if market_conditions and 'avg_volatility' in market_conditions:
                avg_volatility = market_conditions['avg_volatility']
                if avg_volatility > 0.1:  # High volatility
                    max_drawdown *= 0.75  # Reduce allowed drawdown
                    logger_main.info(f"High volatility ({avg_volatility:.4f}), reducing max_drawdown to {max_drawdown:.2%}")
                elif avg_volatility < 0.05:  # Low volatility
                    max_drawdown *= 1.25  # Increase allowed drawdown
                    logger_main.info(f"Low volatility ({avg_volatility:.4f}), increasing max_drawdown to {max_drawdown:.2%}")
            # If drawdown exceeds maximum, prohibit trading
            if drawdown >= max_drawdown:
                logger_main.info(f"Drawdown ({drawdown:.2%}) exceeds maximum ({max_drawdown:.2%}), trading prohibited")
                return 0.0, False
            # Adjust trade percentage
            trade_percentage = self.base_trade_percentage
            # Account for volatility
            if market_conditions and 'avg_volatility' in market_conditions:
                avg_volatility = market_conditions['avg_volatility']
                if avg_volatility > 0.1:  # High volatility
                    trade_percentage *= 0.5  # Reduce by half
                    logger_main.info(f"High volatility ({avg_volatility:.4f}), reducing trade percentage to {trade_percentage:.2%}")
                elif avg_volatility > 0.05:  # Moderate volatility
                    trade_percentage *= 0.75  # Reduce by 25%
                    logger_main.info(f"Moderate volatility ({avg_volatility:.4f}), reducing trade percentage to {trade_percentage:.2%}")
            # Account for trade success rate
            trades = await global_trade_pool.get_all_trades()
            if trades:
                recent_trades = trades[-50:]  # Last 50 trades
                success_rate = sum(1 for trade in recent_trades if trade.get('pnl', 0) > 0) / len(recent_trades)
                if success_rate < 0.4:  # If success rate is below 40%
                    trade_percentage *= 0.5  # Reduce percentage
                    logger_main.info(f"Low trade success rate ({success_rate:.2%}), reducing trade percentage to {trade_percentage:.2%}")
                elif success_rate > 0.7:  # If success rate is above 70%
                    trade_percentage *= 1.5  # Increase percentage
                    logger_main.info(f"High trade success rate ({success_rate:.2%}), increasing trade percentage to {trade_percentage:.2%}")
            return trade_percentage, True
        except Exception as e:
            logger_main.error(f"Error calculating trade percentage: {str(e)}")
            return self.base_trade_percentage, True

# Create a global instance of RiskManager
risk_manager = RiskManager(max_drawdown=0.2, base_trade_percentage=0.1)

__all__ = ['risk_manager']
