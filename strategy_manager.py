from strategies import sma_crossover_strategy, rsi_divergence_strategy, macd_crossover_strategy, bollinger_breakout_strategy, volume_weighted_trend_strategy
from ab_testing import ABTesting
from strategy_generator import StrategyGenerator
import logging

logger = logging.getLogger("main")

class StrategyManager:
    """
    Manage trading strategies with A/B testing and dynamic generation.
    """

    def __init__(self, exchange, symbol, timeframe, since, limit):
        self.strategies = {
            'sma_crossover': sma_crossover_strategy,
            'rsi_divergence': rsi_divergence_strategy,
            'macd_crossover': macd_crossover_strategy,
            'bollinger_breakout': bollinger_breakout_strategy,
            'volume_weighted_trend': volume_weighted_trend_strategy
        }
        self.strategy_params = {
            'rsi_divergence': {'buy_threshold': 30, 'sell_threshold': 70},
            'macd_crossover': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9},
            'bollinger_breakout': {'period': 20, 'std_dev': 2},
            'volume_weighted_trend': {'volume_weight': 1.0}
        }
        self.ab_testing = ABTesting(self.strategies)
        self.generator = StrategyGenerator(exchange, symbol, timeframe, since, limit)
        self.generated_strategies = {}

    async def optimize_strategy_params(self):
        """
        Optimize parameters for all strategies.
        """
        for strategy_name in self.strategies:
            if strategy_name == 'sma_crossover':
                continue
            params = await self.generator.optimize_thresholds(self.generator.exchange, self.generator.symbol, self.generator.timeframe, self.generator.since, self.generator.limit, strategy_name)
            self.strategy_params[strategy_name] = params
            logger.info(f"Optimized parameters for {strategy_name}: {params}")

    async def generate_new_strategy(self, name):
        """
        Generate a new strategy and add it to the pool.

        Args:
            name (str): Name of the new strategy.
        """
        result = await self.generator.generate_strategy()
        weights = result['weights']
        params = result['params']
        new_strategy = self.generator.create_strategy(weights, params)
        self.strategies[name] = new_strategy
        self.strategy_params[name] = params
        self.ab_testing = ABTesting(self.strategies)
        logger.info(f"Generated new strategy {name} with weights {weights} and params {params}")

    def add_strategy(self, name, strategy_func, params=None):
        """
        Add a trading strategy.

        Args:
            name (str): Strategy name.
            strategy_func: Strategy function.
            params (dict): Parameters for the strategy (optional).
        """
        self.strategies[name] = strategy_func
        if params:
            self.strategy_params[name] = params
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
        return self.strategies[name](data, **self.strategy_params.get(name, {}))

    async def ab_test(self, data):
        """
        Run A/B testing on strategies.

        Args:
            data (pd.DataFrame): OHLCV data.

        Returns:
            tuple: (strategy_name, signal)
        """
        strategy_name = await self.ab_testing.select_strategy()
        signal = self.execute_strategy(strategy_name, data)
        return strategy_name, signal

    async def record_result(self, strategy_name, profit):
        """
        Record the result of a strategy for A/B testing.

        Args:
            strategy_name (str): Strategy name.
            profit (float): Profit from the trade.
        """
        await self.ab_testing.record_result(strategy_name, profit)

    async def analyze_ab_results(self):
        """
        Analyze A/B testing results.

        Returns:
            dict: Average profit for each strategy.
        """
        return await self.ab_testing.analyze_results()
