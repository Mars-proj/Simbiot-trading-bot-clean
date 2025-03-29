import asyncio
import ccxt.async_support as ccxt
from bot_trading import start_trading
from config_keys import API_KEYS, PREFERRED_EXCHANGES
from logging_setup import logger_main
from redis_initializer import redis_client
from redis_client import get_json, set_json  # Импортируем функции напрямую

# Ограничиваем количество одновременных запросов к API
MAX_CONCURRENT_REQUESTS = 5
CHECK_INTERVAL = 60  # Интервал проверки в секундах (1 минута)

async def load_markets_for_exchange(exchange_name, exchange_config):
    """Загружает рынки для указанной биржи и кэширует их в Redis"""
    try:
        markets_cache_key = f"markets:{exchange_name}"
        logger_main.debug(f"Checking cached markets for {exchange_name}")
        cached_markets = await get_json(markets_cache_key)  # Используем функцию get_json
        if cached_markets:
            if len(cached_markets) < 10:  # Проверка на минимальное количество символов
                logger_main.warning(f"Cached markets for {exchange_name} are outdated or incomplete: {len(cached_markets)} symbols")
            else:
                logger_main.info(f"Using cached markets for {exchange_name} with {len(cached_markets)} symbols")
                return cached_markets
        logger_main.debug(f"Creating exchange instance for {exchange_name}")
        exchange_class = getattr(ccxt, exchange_name)
        exchange = exchange_class({
            'apiKey': exchange_config['api_key'],
            'secret': exchange_config['api_secret'],
            'enableRateLimit': True,
            'timeout': 30000,  # Тайм-аут на уровне CCXT
        })
        logger_main.debug(f"Starting to load markets for {exchange_name}")
        # Используем низкоуровневый тайм-аут
        task = asyncio.create_task(exchange.load_markets())
        try:
            markets = await asyncio.wait_for(task, timeout=30)
        except asyncio.TimeoutError:
            logger_main.error(f"Timeout while loading markets for {exchange_name} after 30 seconds")
            task.cancel()  # Отменяем задачу
            await exchange.close()
            return None
        logger_main.debug(f"Markets loaded for {exchange_name}: {len(markets)} symbols")
        await set_json(markets_cache_key, markets, expire=86400)  # Используем функцию set_json
        logger_main.info(f"Loaded markets for {exchange_name}: {len(markets)} symbols")
        await exchange.close()
        return markets
    except Exception as e:
        logger_main.error(f"Failed to load markets for {exchange_name}: {str(e)}")
        await exchange.close()
        return None

async def start_trading_with_semaphore(semaphore, user_id):
    """Обёртка для start_trading с использованием семафора"""
    async with semaphore:
        try:
            await start_trading(user_id)
        except Exception as e:
            logger_main.error(f"Failed to start trading for user {user_id}: {str(e)}")
            return e
        return None

async def main():
    """Запускает торговлю для всех пользователей асинхронно в бесконечном цикле"""
    while True:
        try:
            # Получаем список всех пользователей
            users = list(API_KEYS.keys())
            if not users:
                logger_main.error("No users found in API_KEYS")
                await asyncio.sleep(CHECK_INTERVAL)
                continue
            # Собираем уникальные биржи
            exchanges = {}
            for user_id in users:
                exchange_name = PREFERRED_EXCHANGES[user_id]
                if exchange_name not in exchanges:
                    exchanges[exchange_name] = API_KEYS[user_id][exchange_name]
            # Загружаем рынки для каждой биржи
            logger_main.info(f"Loading markets for {len(exchanges)} exchanges: {list(exchanges.keys())}")
            market_tasks = [load_markets_for_exchange(exchange_name, config) for exchange_name, config in exchanges.items()]
            market_results = await asyncio.gather(*market_tasks, return_exceptions=True)
            # Проверяем, для каких бирж удалось загрузить рынки
            valid_exchanges = {}
            for exchange_name, result in zip(exchanges.keys(), market_results):
                if isinstance(result, Exception) or result is None:
                    logger_main.warning(f"Skipping exchange {exchange_name} due to market load error: {str(result)}")
                    continue
                valid_exchanges[exchange_name] = result
            if not valid_exchanges:
                logger_main.error("No valid exchanges to start trading for")
                await asyncio.sleep(CHECK_INTERVAL)
                continue
            # Формируем список пользователей, чьи биржи валидны
            valid_users = [user_id for user_id in users if PREFERRED_EXCHANGES[user_id] in valid_exchanges]
            if not valid_users:
                logger_main.error("No valid users to start trading for after market validation")
                await asyncio.sleep(CHECK_INTERVAL)
                continue
            logger_main.info(f"Starting trading for {len(valid_users)} valid users on exchanges: {list(valid_exchanges.keys())}")
            # Создаём семафор для ограничения количества одновременных запросов
            semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
            # Запускаем торговлю для всех валидных пользователей асинхронно
            trading_tasks = [start_trading_with_semaphore(semaphore, user_id) for user_id in valid_users]
            trading_results = await asyncio.gather(*trading_tasks, return_exceptions=True)
            # Логируем результаты торговли
            for user_id, result in zip(valid_users, trading_results):
                if isinstance(result, Exception):
                    logger_main.warning(f"Trading failed for user {user_id}: {str(result)}")
                else:
                    logger_main.info(f"Trading completed successfully for user {user_id}")
            # Ждём перед следующим циклом
            logger_main.info(f"Waiting {CHECK_INTERVAL} seconds before next trading cycle...")
            await asyncio.sleep(CHECK_INTERVAL)
        except Exception as e:
            logger_main.error(f"Critical error in main loop: {str(e)}")
            logger_main.error("Continuing execution despite error to avoid process crash")
            await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger_main.error(f"Fatal error in start_trading_all.py: {str(e)}")
        raise
