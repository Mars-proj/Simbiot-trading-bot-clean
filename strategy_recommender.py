import numpy as np
import pandas as pd
from logging_setup import logger_main
from utils import log_exception
from global_objects import global_trade_pool, redis_client
import random
import hashlib
import asyncio

class StrategyRecommender:
    def __init__(self, market_conditions=None, user_id=None):
        self.base_population_size = 50  # Base population size
        self.base_generations = 20  # Base number of generations
        self.base_mutation_rate = 0.1  # Base mutation rate
        self.strategies = ['trend', 'momentum', 'volatility', 'volume', 'support_resistance']
        self.user_id = user_id
        # Adapt parameters based on market conditions and trade success
        avg_volatility = market_conditions.get('avg_volatility', 0.0) if market_conditions else 0.0
        success_factor = 1.0
        if user_id:
            recent_trades = asyncio.get_event_loop().run_until_complete(
                global_trade_pool.get_recent_trades(limit=50, user_id=user_id)
            )
            if recent_trades:
                successful_trades = sum(1 for trade in recent_trades if trade.get('pnl', 0) > 0)
                success_rate = successful_trades / len(recent_trades)
                success_factor = 0.5 + success_rate  # Range: 0.5 to 1.5
                self.success_factor = success_factor  # Store for logging in initialize_logging
                self.success_rate = success_rate
        # Adjust population size: larger if volatility is high or success rate is low
        self.population_size = int(self.base_population_size * (1 + avg_volatility) * (2 - success_factor))
        self.population_size = max(30, min(100, self.population_size))
        # Adjust generations: fewer if volatility is high, more if success rate is low
        self.generations = int(self.base_generations * (1 - avg_volatility / 2) * (2 - success_factor))
        self.generations = max(10, min(30, self.generations))
        # Adjust mutation rate: higher if volatility is high or success rate is low
        self.mutation_rate = self.base_mutation_rate * (1 + avg_volatility) * (2 - success_factor)
        self.mutation_rate = max(0.05, min(0.3, self.mutation_rate))
        self.avg_volatility = avg_volatility  # Store for logging
        self.market_conditions = market_conditions  # Store for initialize_logging

    def initialize_logging(self):
        """Initializes logging for StrategyRecommender"""
        logger_main.info(f"Adapted evolution parameters: population_size={self.population_size}, generations={self.generations}, mutation_rate={self.mutation_rate:.2f} (volatility={self.avg_volatility:.4f}, success_factor={self.success_factor if hasattr(self, 'success_factor') else 1.0:.2f})")
        if self.user_id and hasattr(self, 'success_rate'):
            logger_main.info(f"Recent trade success rate for {self.user_id}: {self.success_rate:.2f}, success_factor: {self.success_factor:.2f}")
        # Initialize the strategy population after logging is set up
        self.strategy_population = self._initialize_population(self.market_conditions)

    def _initialize_population(self, market_conditions=None):
        """Initializes the initial population of strategies"""
        logger_main.info("Initializing strategy population")
        strategies = []
        # Adjust parameter ranges based on market conditions
        volatility = market_conditions.get('avg_volatility', 0.0) if market_conditions else 0.0
        rsi_buy_range = (15, 35) if volatility > 0.1 else (20, 40)  # More aggressive during high volatility
        rsi_sell_range = (65, 85) if volatility > 0.1 else (60, 80)
        volatility_threshold_range = (0.01, 0.05) if volatility > 0.1 else (0.02, 0.1)
        for _ in range(self.population_size):
            strategy = {
                'strategy_name': random.choice(self.strategies),
                'rsi_buy': random.uniform(*rsi_buy_range),
                'rsi_sell': random.uniform(*rsi_sell_range),
                'stop_loss_percentage': random.uniform(0.01, 0.05),
                'take_profit_drop': random.uniform(0.01, 0.05),
                'sma_short_window': random.randint(10, 30),
                'sma_long_window': random.randint(40, 70),
                'volatility_threshold': random.uniform(*volatility_threshold_range),
                'fitness': 0.0  # Will be computed later
            }
            strategies.append(strategy)
        return strategies

    async def evaluate_strategy(self, strategy, trades, ohlcv, success_prob=None):
        """Evaluates a strategy based on historical data"""
        logger_main.info(f"Evaluating strategy: {strategy}")
        try:
            # Create a unique cache key for the strategy
            strategy_key = hashlib.md5(str(strategy).encode()).hexdigest()
            cache_key = f"strategy_fitness:{strategy_key}"
            cached_fitness = await redis_client.get_json(cache_key)
            if cached_fitness is not None:
                logger_main.debug(f"Using cached fitness for strategy: {cached_fitness}")
                return cached_fitness
            df = ohlcv.copy()
            df['sma_short'] = df['close'].rolling(window=int(strategy['sma_short_window'])).mean()
            df['sma_long'] = df['close'].rolling(window=int(strategy['sma_long_window'])).mean()
            df['rsi'] = pd.Series(pd.DataFrame({'close': df['close']}).ta.rsi(length=14))
            df['returns'] = df['close'].pct_change()
            df['volatility'] = df['returns'].rolling(window=20).std() * np.sqrt(252)
            # Calculate MACD
            macd_df = pd.DataFrame({'close': df['close']}).ta.macd(fast=12, slow=26, signal=9)
            df['macd'] = macd_df['MACD_12_26_9']
            df['macd_signal'] = macd_df['MACDs_12_26_9']
            position = 0
            entry_price = 0
            total_pnl = 0
            trades_made = 0
            pnls = []
            for i in range(len(df)):
                current_price = df['close'].iloc[i]
                current_rsi = df['rsi'].iloc[i]
                sma_short = df['sma_short'].iloc[i]
                sma_long = df['sma_long'].iloc[i]
                volatility = df['volatility'].iloc[i]
                macd = df['macd'].iloc[i]
                macd_signal = df['macd_signal'].iloc[i]
                if pd.isna(current_rsi) or pd.isna(sma_short) or pd.isna(sma_long) or pd.isna(macd) or pd.isna(macd_signal):
                    continue
                # Entry point
                if position == 0:
                    if (sma_short > sma_long and
                        current_rsi < strategy['rsi_buy'] and
                        (volatility < strategy['volatility_threshold'] or np.isnan(volatility)) and
                        macd > macd_signal):
                        # Filter by success_prob
                        if success_prob is not None and success_prob < 0.5:
                            continue
                        position = 1  # Buy
                        entry_price = current_price
                        trades_made += 1
                # Exit point
                if position == 1:
                    stop_loss_price = entry_price * (1 - strategy['stop_loss_percentage'])
                    take_profit_price = entry_price * (1 + strategy['take_profit_drop'])
                    if current_price <= stop_loss_price:
                        trade_pnl = (current_price - entry_price) / entry_price * 100
                        total_pnl += trade_pnl
                        pnls.append(trade_pnl)
                        position = 0
                    elif current_price >= take_profit_price:
                        trade_pnl = (current_price - entry_price) / entry_price * 100
                        total_pnl += trade_pnl
                        pnls.append(trade_pnl)
                        position = 0
                    elif sma_short < sma_long and current_rsi > strategy['rsi_sell'] and macd < macd_signal:
                        trade_pnl = (current_price - entry_price) / entry_price * 100
                        total_pnl += trade_pnl
                        pnls.append(trade_pnl)
                        position = 0
            # Calculate fitness: average PNL per trade, adjusted for trade count and stability
            avg_pnl = total_pnl / trades_made if trades_made > 0 else 0
            trade_count_factor = min(trades_made / 10, 1.0)  # Encourage more trades
            stability = np.std(pnls) if pnls else 0
            stability_factor = 1.0 / (1 + stability) if stability > 0 else 1.0  # Penalize high variance
            fitness = avg_pnl * trade_count_factor * stability_factor
            logger_main.info(f"Strategy fitness: {fitness:.2f} (avg_pnl: {avg_pnl:.2f}, trades: {trades_made}, stability_factor: {stability_factor:.2f})")
            # Cache the fitness
            await redis_client.set_json(cache_key, fitness, expire=3600)  # Cache for 1 hour
            return fitness
        except Exception as e:
            logger_main.error(f"Error evaluating strategy: {str(e)}")
            return 0.0

    async def evolve_strategies(self, ohlcv, success_prob=None, market_conditions=None):
        """Evolves strategies using a genetic algorithm"""
        logger_main.info("Starting strategy evolution")
        trades = await global_trade_pool.get_all_trades()
        logger_main.info(f"Retrieved {len(trades)} trades for strategy evolution")
        for generation in range(self.generations):
            logger_main.info(f"Generation {generation + 1}/{self.generations}")
            # Evaluate fitness of each strategy
            for strategy in self.strategy_population:
                strategy['fitness'] = await self.evaluate_strategy(strategy, trades, ohlcv, success_prob)
            # Sort by fitness
            self.strategy_population.sort(key=lambda x: x['fitness'], reverse=True)
            # Preserve the best strategies (elitism)
            new_population = self.strategy_population[:10]  # Top 10 remain
            # Crossover and mutation to create new strategies
            while len(new_population) < self.population_size:
                parent1 = random.choice(self.strategy_population[:20])
                parent2 = random.choice(self.strategy_population[:20])
                # Crossover: weighted average based on fitness
                weight1 = parent1['fitness'] / (parent1['fitness'] + parent2['fitness'] + 1e-10)
                weight2 = 1 - weight1
                child = {
                    'strategy_name': random.choice([parent1['strategy_name'], parent2['strategy_name']]),
                    'rsi_buy': parent1['rsi_buy'] * weight1 + parent2['rsi_buy'] * weight2,
                    'rsi_sell': parent1['rsi_sell'] * weight1 + parent2['rsi_sell'] * weight2,
                    'stop_loss_percentage': parent1['stop_loss_percentage'] * weight1 + parent2['stop_loss_percentage'] * weight2,
                    'take_profit_drop': parent1['take_profit_drop'] * weight1 + parent2['take_profit_drop'] * weight2,
                    'sma_short_window': int(parent1['sma_short_window'] * weight1 + parent2['sma_short_window'] * weight2),
                    'sma_long_window': int(parent1['sma_long_window'] * weight1 + parent2['sma_long_window'] * weight2),
                    'volatility_threshold': parent1['volatility_threshold'] * weight1 + parent2['volatility_threshold'] * weight2,
                    'fitness': 0.0
                }
                # Mutation: adjust based on market conditions
                if random.random() < self.mutation_rate:
                    volatility = market_conditions.get('avg_volatility', 0.0) if market_conditions else 0.0
                    rsi_buy_range = (10, 30) if volatility > 0.1 else (20, 40)
                    rsi_sell_range = (70, 90) if volatility > 0.1 else (60, 80)
                    volatility_threshold_range = (0.01, 0.05) if volatility > 0.1 else (0.02, 0.1)
                    child['strategy_name'] = random.choice(self.strategies)
                    child['rsi_buy'] = random.uniform(*rsi_buy_range)
                    child['rsi_sell'] = random.uniform(*rsi_sell_range)
                    child['stop_loss_percentage'] = random.uniform(0.01, 0.05)
                    child['take_profit_drop'] = random.uniform(0.01, 0.05)
                    child['sma_short_window'] = random.randint(10, 30)
                    child['sma_long_window'] = random.randint(40, 70)
                    child['volatility_threshold'] = random.uniform(*volatility_threshold_range)
                new_population.append(child)
            self.strategy_population = new_population
        # Return the best strategy
        best_strategy = self.strategy_population[0]
        logger_main.info(f"Best strategy after evolution: {best_strategy}")
        return best_strategy

    async def recommend_strategy(self, ohlcv, success_prob=None, market_conditions=None):
        """Recommends a strategy based on the evolutionary algorithm"""
        logger_main.info("Recommending strategy")
        best_strategy = await self.evolve_strategies(ohlcv, success_prob, market_conditions)
        return best_strategy

__all__ = ['StrategyRecommender']
