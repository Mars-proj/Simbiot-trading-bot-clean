import pandas as pd
import numpy as np
from genetic_optimizer import GeneticOptimizer
from strategies import sma_crossover_strategy, rsi_divergence_strategy, macd_crossover_strategy, bollinger_breakout_strategy, volume_weighted_trend_strategy
import logging

logger = logging.getLogger("main")

class StrategyGenerator:
    """
    Generate new trading strategies using genetic algorithms and historical data.
    """

    def __init__(self, exchange, symbol, timeframe, since, limit):
        """
        Initialize the strategy generator.

        Args:
            exchange: Exchange instance.
            symbol (str): Trading symbol.
            timeframe (str): Timeframe for OHLCV data.
            since (int): Timestamp to fetch from (in milliseconds).
            limit (int): Number of candles to fetch.
        """
        self.exchange = exchange
        self.symbol = symbol
        self.timeframe = timeframe
        self.since = since
        self.limit = limit
        self.strategies = {
            "sma_crossover": sma_crossover_strategy,
            "rsi_divergence": rsi_divergence_strategy,
            "macd_crossover": macd_crossover_strategy,
            "bollinger_breakout": bollinger_breakout_strategy,
            "volume_weighted_trend": volume_weighted_trend_strategy
        }
        self.strategy_params = {
            "rsi_divergence": {"buy_threshold": 30, "sell_threshold": 70},
            "macd_crossover": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
            "bollinger_breakout": {"period": 20, "std_dev": 2},
            "volume_weighted_trend": {"volume_weight": 1.0}
        }

    async def fetch_data(self):
        """
        Fetch historical OHLCV data.

        Returns:
            pd.DataFrame: Historical data.
        """
        ohlcv = await self.exchange.fetch_ohlcv(self.symbol, self.timeframe, since=self.since, limit=self.limit)
        return pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    async def evaluate_strategy(self, individual):
        """
        Evaluate a strategy combination using backtesting.

        Args:
            individual (list): Strategy weights and parameters.

        Returns:
            tuple: Fitness value (average profit).
        """
        from backtest_cycle import run_backtest_cycle

        weights = individual[:len(self.strategies)]  # Веса для стратегий
        params = individual[len(self.strategies):]  # Параметры для стратегий

        # Нормализуем веса
        total_weight = sum(weights)
        if total_weight == 0:
            total_weight = 1
        weights = [w / total_weight for w in weights]

        # Распределяем параметры
        param_idx = 0
        strategy_params = {}
        for strategy_name in self.strategies.keys():
            if strategy_name == "sma_crossover":
                strategy_params[strategy_name] = {}
            elif strategy_name == "rsi_divergence":
                strategy_params[strategy_name] = {
                    "buy_threshold": params[param_idx] * 100,
                    "sell_threshold": params[param_idx + 1] * 100
                }
                param_idx += 2
            elif strategy_name == "macd_crossover":
                strategy_params[strategy_name] = {
                    "fast_period": int(params[param_idx] * 20 + 5),
                    "slow_period": int(params[param_idx + 1] * 40 + 10),
                    "signal_period": int(params[param_idx + 2] * 10 + 3)
                }
                param_idx += 3
            elif strategy_name == "bollinger_breakout":
                strategy_params[strategy_name] = {
                    "period": int(params[param_idx] * 20 + 10),
                    "std_dev": params[param_idx + 1] * 2 + 1
                }
                param_idx += 2
            elif strategy_name == "volume_weighted_trend":
                strategy_params[strategy_name] = {
                    "volume_weight": params[param_idx] * 2
                }
                param_idx += 1

        # Комбинированная стратегия
        data = await self.fetch_data()
        signals = []
        for i in range(len(data)):
            window = data.iloc[:i+1]
            combined_signal = 0
            for idx, (strategy_name, strategy_func) in enumerate(self.strategies.items()):
                signal = strategy_func(window, **strategy_params.get(strategy_name, {}))
                signal_value = 1 if signal == "buy" else -1 if signal == "sell" else 0
                combined_signal += weights[idx] * signal_value
            signals.append("buy" if combined_signal > 0 else "sell" if combined_signal < 0 else "hold")

        # Бэктестинг
        result = await run_backtest_cycle(self.exchange, self.symbol, self.timeframe, self.since, self.limit, strategy_func=lambda d: signals[d.index[-1]])
        return (result['final_balance'],)

    async def generate_strategy(self, generations=10, population_size=50):
        """
        Generate a new trading strategy using genetic algorithms.

        Args:
            generations (int): Number of generations (default: 10).
            population_size (int): Population size (default: 50).

        Returns:
            dict: Generated strategy (weights and parameters).
        """
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)

        toolbox = base.Toolbox()
        # Веса для стратегий (5 стратегий)
        for i in range(len(self.strategies)):
            toolbox.register(f"weight_{i}", random.uniform, 0, 1)
        # Параметры: 2 для RSI, 3 для MACD, 2 для BB, 1 для VW
        for i in range(8):
            toolbox.register(f"param_{i}", random.uniform, 0, 1)
        toolbox.register("individual", tools.initCycle, creator.Individual,
                        [toolbox.__getattribute__(f"weight_{i}") for i in range(len(self.strategies))] +
                        [toolbox.__getattribute__(f"param_{i}") for i in range(8)], n=1)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register("evaluate", self.evaluate)
        toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1, indpb=0.2)
        toolbox.register("select", tools.selTournament, tournsize=3)

        population = toolbox.population(n=population_size)
        for gen in range(generations):
            offspring = algorithms.varAnd(population, toolbox, cxpb=0.5, mutpb=0.2)
            fits = await asyncio.gather(*[toolbox.evaluate(ind) for ind in offspring])
            for fit, ind in zip(fits, offspring):
                ind.fitness.values = fit
            population = toolbox.select(offspring, k=len(population))
        best = tools.selBest(population, k=1)[0]

        weights = best[:len(self.strategies)]
        total_weight = sum(weights)
        if total_weight == 0:
            total_weight = 1
        weights = [w / total_weight for w in weights]

        param_idx = 0
        strategy_params = {}
        for strategy_name in self.strategies.keys():
            if strategy_name == "sma_crossover":
                strategy_params[strategy_name] = {}
            elif strategy_name == "rsi_divergence":
                strategy_params[strategy_name] = {
                    "buy_threshold": best[len(self.strategies) + param_idx] * 100,
                    "sell_threshold": best[len(self.strategies) + param_idx + 1] * 100
                }
                param_idx += 2
            elif strategy_name == "macd_crossover":
                strategy_params[strategy_name] = {
                    "fast_period": int(best[len(self.strategies) + param_idx] * 20 + 5),
                    "slow_period": int(best[len(self.strategies) + param_idx + 1] * 40 + 10),
                    "signal_period": int(best[len(self.strategies) + param_idx + 2] * 10 + 3)
                }
                param_idx += 3
            elif strategy_name == "bollinger_breakout":
                strategy_params[strategy_name] = {
                    "period": int(best[len(self.strategies) + param_idx] * 20 + 10),
                    "std_dev": best[len(self.strategies) + param_idx + 1] * 2 + 1
                }
                param_idx += 2
            elif strategy_name == "volume_weighted_trend":
                strategy_params[strategy_name] = {
                    "volume_weight": best[len(self.strategies) + param_idx] * 2
                }
                param_idx += 1

        return {
            "weights": dict(zip(self.strategies.keys(), weights)),
            "params": strategy_params
        }

    def create_strategy(self, weights, params):
        """
        Create a combined strategy function.

        Args:
            weights (dict): Weights for each strategy.
            params (dict): Parameters for each strategy.

        Returns:
            function: Combined strategy function.
        """
        def combined_strategy(data):
            combined_signal = 0
            for strategy_name, strategy_func in self.strategies.items():
                signal = strategy_func(data, **params.get(strategy_name, {}))
                signal_value = 1 if signal == "buy" else -1 if signal == "sell" else 0
                combined_signal += weights[strategy_name] * signal_value
            return "buy" if combined_signal > 0 else "sell" if combined_signal < 0 else "hold"
        return combined_strategy
