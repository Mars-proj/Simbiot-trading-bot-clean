from strategies import sma_strategy, rsi_strategy
from ab_testing import ABTesting

class StrategyManager:
    """
    Manage trading strategies with A/B testing.
    """

    def __init__(self):
        self.strategies = {
            'sma': sma_strategy,
            'rsi': rsi_strategy,
        }
        self.ab_testing = ABTesting(self.strategies)

    def add_strategy(self, name, strategy_func):
        """
        Add a trading strategy.

        Args:
            name (str): Strategy name.
            strategy_func: Strategy function.
        """
        self.strategies[name] = strategy_func
        self.ab_testing = ABTesting(self.strategies)

    def execute_strategy(self, name, data):
        """
        Execute a trading strategy.

        Args:
            name (str): Strategy name.
            data (pd.DataFrame): OHLCV data.

        Returns:
            str: Trading signal.
        """
        if name not in self.strategies:
            raise ValueError(f"Strategy {name} not found")
        return self.strategies[name](data)

    def ab_test(self, data):
        """
        Run A/B testing on strategies.

        Args:
            data (pd.DataFrame): OHLCV data.

        Returns:
            tuple: (strategy_name, signal)
        """
        strategy_name = self.ab_testing.select_strategy()
        signal = self.execute_strategy(strategy_name, data)
        return strategy_name, signal

    def record_result(self, strategy_name, profit):
        """
        Record the result of a strategy for A/B testing.

        Args:
            strategy_name (str): Strategy name.
            profit (float): Profit from the trade.
        """
        self.ab_testing.record_result(strategy_name, profit)

    def analyze_ab_results(self):
        """
        Analyze A/B testing results.

        Returns:
            dict: Average profit for each strategy.
        """
        return self.ab_testing.analyze_results()
