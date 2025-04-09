import random
from statistics import mean

class ABTesting:
    """
    Manage A/B testing for trading strategies.
    """

    def __init__(self, strategies):
        """
        Initialize A/B testing.

        Args:
            strategies (dict): Dictionary of strategy names and functions.
        """
        self.strategies = strategies
        self.results = {name: [] for name in strategies}

    def select_strategy(self, weights=None):
        """
        Select a strategy for A/B testing.

        Args:
            weights (dict): Weights for each strategy (default: equal weights).

        Returns:
            str: Selected strategy name.
        """
        if weights is None:
            weights = {name: 1/len(self.strategies) for name in self.strategies}
        return random.choices(list(self.strategies.keys()), weights=list(weights.values()), k=1)[0]

    def record_result(self, strategy_name, profit):
        """
        Record the result of a strategy.

        Args:
            strategy_name (str): Strategy name.
            profit (float): Profit from the trade.
        """
        self.results[strategy_name].append(profit)

    def analyze_results(self):
        """
        Analyze A/B testing results.

        Returns:
            dict: Average profit for each strategy.
        """
        return {name: mean(profits) if profits else 0 for name, profits in self.results.items()}
