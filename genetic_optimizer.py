from deap import base, creator, tools, algorithms
import random

class GeneticOptimizer:
    """
    Optimize parameters using genetic algorithms.
    """

    def __init__(self, evaluate_func, param_ranges):
        """
        Initialize the genetic optimizer.

        Args:
            evaluate_func: Function to evaluate fitness of parameters.
            param_ranges: List of tuples (min, max) for each parameter.
        """
        self.evaluate_func = evaluate_func
        self.param_ranges = param_ranges

    def optimize(self, generations=10, population_size=50):
        """
        Run genetic optimization.

        Args:
            generations (int): Number of generations (default: 10).
            population_size (int): Population size (default: 50).

        Returns:
            list: Best parameters.
        """
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)

        toolbox = base.Toolbox()
        for i, (min_val, max_val) in enumerate(self.param_ranges):
            toolbox.register(f"attr_float_{i}", random.uniform, min_val, max_val)
        toolbox.register("individual", tools.initCycle, creator.Individual,
                        [toolbox.__getattribute__(f"attr_float_{i}") for i in range(len(self.param_ranges))], n=1)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register("evaluate", self.evaluate_func)
        toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1, indpb=0.2)
        toolbox.register("select", tools.selTournament, tournsize=3)

        population = toolbox.population(n=population_size)
        for gen in range(generations):
            offspring = algorithms.varAnd(population, toolbox, cxpb=0.5, mutpb=0.2)
            fits = toolbox.map(toolbox.evaluate, offspring)
            for fit, ind in zip(fits, offspring):
                ind.fitness.values = fit
            population = toolbox.select(offspring, k=len(population))
        best = tools.selBest(population, k=1)[0]
        return best
