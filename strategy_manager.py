from strategies import sma_crossover_strategy, rsi_divergence_strategy, macd_crossover_strategy, bollinger_breakout_strategy, volume_weighted_trend_strategy
from strategy_param_generator import generate_strategy_params  # Обновляем имя модуля
import logging

logger = logging.getLogger(__name__)

class StrategyManager:
    def __init__(self):
        self.strategies = {
            'sma': sma_crossover_strategy,
            'rsi': rsi_divergence_strategy,
            'macd': macd_crossover_strategy,
            'bollinger': bollinger_breakout_strategy,
            'volume': volume_weighted_trend_strategy
        }
        self.param_ranges = {
            'sma': {'short_window': (10, 30), 'long_window': (40, 60)},
            'rsi': {'rsi_window': (10, 20), 'rsi_overbought': (60, 80), 'rsi_oversold': (20, 40)},
            'macd': {'short_window': (10, 15), 'long_window': (20, 30), 'signal_window': (5, 10)},
            'bollinger': {'window': (15, 25), 'num_std': (1, 3)},
            'volume': {'volume_window': (10, 30)}
        }

    def get_strategy(self, strategy_type):
        """
        Get a strategy function by type.

        Args:
            strategy_type: Type of strategy ('sma', 'rsi', 'macd', 'bollinger', 'volume').

        Returns:
            function: Strategy function.
        """
        if strategy_type not in self.strategies:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        return self.strategies[strategy_type]

    def generate_params(self, strategy_type):
        """
        Generate parameters for a given strategy type.

        Args:
            strategy_type: Type of strategy ('sma', 'rsi', 'macd', 'bollinger', 'volume').

        Returns:
            dict: Generated parameters.
        """
        return generate_strategy_params(strategy_type, self.param_ranges)
