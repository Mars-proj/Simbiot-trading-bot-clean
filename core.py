# core.py
import logging
from user_manager import UserManager
from exchange_pool import ExchangePool
from symbol_filter import filter_symbols
from start_trading_all import start_trading_all
from market_state_analyzer import analyze_market_state
import asyncio
import concurrent.futures
from datetime import datetime
import time
import redis.asyncio as redis
import json
import psutil
import os

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('main')

async def get_redis_client():
    """Инициализация Redis клиента."""
    return await redis.from_url("redis://localhost:6379/0")

async def update_signal_stats(signal_count):
    """Обновляет статистику сигналов в Redis и возвращает адаптивный интервал."""
    redis_client = await get_redis_client()
    try:
        stats_key = "signal_stats"
        stats_data = await redis_client.get(stats_key)
        if stats_data:
            stats_data = json.loads(stats_data.decode())
        else:
            stats_data = {'signal_counts': [], 'last_cycles': 5}

        stats_data['signal_counts'].append(signal_count)
        stats_data['signal_counts'] = stats_data['signal_counts'][-stats_data['last_cycles']:]

        avg_signals = sum(stats_data['signal_counts']) / len(stats_data['signal_counts']) if stats_data['signal_counts'] else 0

        base_interval = 300
        if avg_signals > 10:
            interval = max(60, base_interval * 0.5)
        elif avg_signals < 2:
            interval = min(600, base_interval * 2)
        else:
            interval = base_interval

        await redis_client.set(stats_key, json.dumps(stats_data), ex=86400 * 30)
        return interval
    finally:
        await redis_client.close()

async def process_user(user, credentials, since, limit, timeframe):
    """Обрабатывает одного пользователя."""
    start_time = time.time()
    signal_count = 0
    try:
        logger.info(f"Processing symbols for user {user} with credentials: {credentials}")
        exchange_pool = ExchangePool(credentials['api_key'], credentials['api_secret'], user)
        async with exchange_pool as exchange:
            logger.debug(f"Exchange object created for user {user}: {exchange}")
            logger.debug(f"Calling analyze_market_state for user {user}")
            market_state, symbols = await analyze_market_state(exchange_pool, timeframe)
            logger.info(f"Market state for user {user}: {market_state}")
            if market_state['trend'] == 'neutral' and market_state['volatility'] == 0.01:
                logger.warning(f"Using default market state for user {user} due to analysis failure")
            if not symbols:
                logger.error(f"No symbols available for user {user}, skipping")
                return signal_count
            logger.debug(f"Calling filter_symbols for user {user} with {len(symbols)} symbols")
            valid_symbols = await filter_symbols(exchange_pool, symbols, since, limit, timeframe, user, market_state)
            logger.info(f"Filtered symbols for user {user}: {valid_symbols}")
            logger.debug(f"Calling start_trading_all for user {user}")
            signal_count = await start_trading_all(exchange, valid_symbols, user, market_state)
            logger.info(f"Completed processing for user {user} with {len(valid_symbols)} valid symbols, generated {signal_count} signals")
    except Exception as e:
        logger.error(f"Error processing user {user}: {type(e).__name__}: {str(e)}")
    finally:
        duration = time.time() - start_time
        logger.info(f"User {user} processing took {duration:.2f} seconds")
    return signal_count

async def log_system_metrics():
    """Логирует метрики системы: использование CPU, памяти и количество активных пользователей."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_used = memory.used / (1024 * 1024)  # MB
        memory_total = memory.total / (1024 * 1024)  # MB
        memory_percent = memory.percent
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info().rss / (1024 * 1024)  # MB

        redis_client = await get_redis_client()
        try:
            users = await redis_client.get("users")
            active_users = len(json.loads(users.decode())) if users else 0
        finally:
            await redis_client.close()

        logger.info(f"System metrics: CPU={cpu_percent}%, Memory={memory_used:.2f}/{memory_total:.2f}MB ({memory_percent}%), Process Memory={process_memory:.2f}MB, Active Users={active_users}")
    except Exception as e:
        logger.error(f"Failed to log system metrics: {type(e).__name__}: {str(e)}")

async def main():
    user_manager = UserManager()
    try:
        cycle_count = 0
        max_concurrent_tasks = 100
        cycle_times = []
        while True:
            cycle_count += 1
            logger.info(f"Starting cycle {cycle_count}")
            start_time = time.time()

            current_timestamp = int(datetime.now().timestamp() * 1000)
            since = current_timestamp - (30 * 24 * 60 * 60 * 1000)  # 30 дней назад
            limit = 1000
            timeframe = '4h'

            logger.debug("Loading users from Redis")
            users = await user_manager.get_users()
            logger.info(f"Loaded {len(users)} users from Redis: {users}")

            total_signals = 0
            tasks = []
            for user, credentials in users.items():
                tasks.append(process_user(user, credentials, since, limit, timeframe))

            for i in range(0, len(tasks), max_concurrent_tasks):
                batch = tasks[i:i + max_concurrent_tasks]
                batch_results = await asyncio.gather(*batch, return_exceptions=True)
                for result in batch_results:
                    if isinstance(result, int):
                        total_signals += result
                logger.info(f"Processed batch of {len(batch)} users")

            # Мониторинг производительности
            cycle_duration = time.time() - start_time
            cycle_times.append(cycle_duration)
            cycle_times = cycle_times[-5:]
            avg_cycle_time = sum(cycle_times) / len(cycle_times) if cycle_times else 0
            logger.info(f"Cycle {cycle_count} completed in {cycle_duration:.2f} seconds, average cycle time: {avg_cycle_time:.2f} seconds, total signals: {total_signals}")

            # Динамическое управление max_concurrent_tasks
            if avg_cycle_time > 300:
                max_concurrent_tasks = max(50, max_concurrent_tasks - 10)
                logger.info(f"Reducing max_concurrent_tasks to {max_concurrent_tasks} due to high cycle time")
            elif avg_cycle_time < 60:
                max_concurrent_tasks = min(200, max_concurrent_tasks + 10)
                logger.info(f"Increasing max_concurrent_tasks to {max_concurrent_tasks} due to low cycle time")

            # Логирование системных метрик
            await log_system_metrics()

            # Адаптивный интервал
            interval = await update_signal_stats(total_signals)
            logger.info(f"Waiting for {interval} seconds before next cycle")
            await asyncio.sleep(interval)

    except Exception as e:
        logger.error(f"Error in main loop: {type(e).__name__}: {str(e)}")
    finally:
        logger.debug("Closing user manager")
        await user_manager.close()

if __name__ == "__main__":
    logger.debug("Starting main execution")
    asyncio.run(main())
