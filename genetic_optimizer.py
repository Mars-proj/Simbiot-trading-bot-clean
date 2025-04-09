from deap import base, creator, tools, algorithms
import random
from backtest_cycle import run_backtest_cycle
import ccxt.async_support as ccxt
import asyncio

class GeneticOptimizer:
    """
    Optimize parameters using genetic algorithms with backtesting.
    """

    def __init__(self, exchange, symbol, timeframe, since, limit):
        """
        Initialize the genetic optimizer.

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

    async def evaluate(self, individual):
        """
        Evaluate the fitness of parameters using backtesting.

        Args:
            individual (list): Parameters to evaluate (profit_target, stop_loss, trailing_percent).

        Returns:
            tuple: Fitness value (final balance).
        """
        profit_target, stop_loss, trailing_percent = individual
        result = await run_backtest_cycle(
            self.exchange, self.symbol, self.timeframe, self.since, self.limit,
            profit_target=profit_target, stop_loss=stop_loss
        )
        return (result['final_balance'],)

    async def optimize(self, generations=10, population_size=50):
        """
        Run genetic optimization.

        Args:
            generations (int): Number of generations (default: 10).
            population_size (int): Population size (default: 50).

        Returns:
            dict: Best parameters.
        """
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)

        toolbox = base.Toolbox()
        param_ranges = [(0.01, 0.1), (0.01, 0.05), (0.005, 0.02)]  # profit_target, stop_loss, trailing_percent
        for i, (min_val, max_val) in enumerate(param_ranges):
            toolbox.register(f"attr_float_{i}", random.uniform, min_val, max_val)
        toolbox.register("individual", tools.initCycle, creator.Individual,
                        [toolbox.__getattribute__(f"attr_float_{i}") for i in range(len(param_ranges))], n=1)
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
        return {
            "profit_target": best[0],
            "stop_loss": best[1],
            "trailing_percent": best[2]
        }
