import json
import time
from logging_setup import logger_main, logger_exceptions
from redis_initializer import redis_client

async def get_json(key):
    """Получает данные из Redis и десериализует их из JSON"""
    start_time = time.time()
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger_main.error(f"Error getting JSON from Redis for key {key}: {str(e)}")
        logger_exceptions.error(f"Error getting JSON: {str(e)}", exc_info=True)
        return None
    finally:
        logger_main.debug(f"get_json for key {key} took {time.time() - start_time:.3f} seconds")

async def set_json(key, value, expire=None):
    """Сериализует данные в JSON и сохраняет их в Redis"""
    start_time = time.time()
    try:
        serialized = json.dumps(value)
        if expire:
            await redis_client.setex(key, expire, serialized)
        else:
            await redis_client.set(key, serialized)
    except Exception as e:
        logger_main.error(f"Error setting JSON to Redis for key {key}: {str(e)}")
        logger_exceptions.error(f"Error setting JSON: {str(e)}", exc_info=True)
    finally:
        logger_main.debug(f"set_json for key {key} took {time.time() - start_time:.3f} seconds")

async def get_trades_from_cache(user_id):
    """Получает сделки пользователя из кэша Redis"""
    start_time = time.time()
    try:
        trades_key = f"trades:{user_id}"
        trades = await redis_client.lrange(trades_key, 0, -1)
        return [json.loads(trade) for trade in trades]
    except Exception as e:
        logger_main.error(f"Error getting trades from cache for user {user_id}: {str(e)}")
        logger_exceptions.error(f"Error getting trades: {str(e)}", exc_info=True)
        return []
    finally:
        logger_main.debug(f"get_trades_from_cache for user {user_id} took {time.time() - start_time:.3f} seconds")

async def add_trade_to_cache(user_id, trade_info):
    """Добавляет сделку в кэш Redis"""
    start_time = time.time()
    try:
        trades_key = f"trades:{user_id}"
        serialized = json.dumps(trade_info)
        await redis_client.lpush(trades_key, serialized)
        # Ограничиваем длину списка до 100 сделок
        await redis_client.ltrim(trades_key, 0, 99)
        # Устанавливаем срок жизни ключа (например, 7 дней)
        await redis_client.expire(trades_key, 7 * 24 * 60 * 60)
    except Exception as e:
        logger_main.error(f"Error adding trade to cache for user {user_id}: {str(e)}")
        logger_exceptions.error(f"Error adding trade: {str(e)}", exc_info=True)
    finally:
        logger_main.debug(f"add_trade_to_cache for user {user_id} took {time.time() - start_time:.3f} seconds")

async def add_to_problematic_symbols(symbol, exchange_name):
    """Добавляет проблемный символ в кэш Redis"""
    start_time = time.time()
    try:
        problematic_key = f"problematic_symbols:{exchange_name}"
        await redis_client.sadd(problematic_key, symbol)
        # Устанавливаем срок жизни ключа (например, 30 дней)
        await redis_client.expire(problematic_key, 30 * 24 * 60 * 60)
        logger_main.info(f"Added {symbol} to problematic symbols for {exchange_name}")
    except Exception as e:
        logger_main.error(f"Error adding {symbol} to problematic symbols for {exchange_name}: {str(e)}")
        logger_exceptions.error(f"Error adding problematic symbol: {str(e)}", exc_info=True)
    finally:
        logger_main.debug(f"add_to_problematic_symbols for {symbol} took {time.time() - start_time:.3f} seconds")

async def get_problematic_symbols(exchange_name):
    """Получает список проблемных символов для биржи из кэша Redis"""
    start_time = time.time()
    try:
        problematic_key = f"problematic_symbols:{exchange_name}"
        symbols = await redis_client.smembers(problematic_key)
        return set(symbols) if symbols else set()  # Убираем decode, так как decode_responses=True
    except Exception as e:
        logger_main.error(f"Error getting problematic symbols for {exchange_name}: {str(e)}")
        logger_exceptions.error(f"Error getting problematic symbols: {str(e)}", exc_info=True)
        return set()
    finally:
        logger_main.debug(f"get_problematic_symbols for {exchange_name} took {time.time() - start_time:.3f} seconds")

__all__ = ['get_json', 'set_json', 'get_trades_from_cache', 'add_trade_to_cache', 'add_to_problematic_symbols', 'get_problematic_symbols']
