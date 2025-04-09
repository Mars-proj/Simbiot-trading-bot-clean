# symbol_filter.py
import logging
import asyncio
import redis.asyncio as redis
import json
import time

logger = logging.getLogger("main")

async def get_redis_client():
    """Инициализация Redis клиента."""
    return await redis.from_url("redis://localhost:6379/0")

async def filter_symbols(exchange, symbols, since, limit, timeframe, user=None, market_state=None, batch_size=500):
    """Фильтрует символы, оставляя только пары с USDT и достаточным объёмом торгов, по батчам."""
    redis_client = await get_redis_client()
    try:
        valid_symbols = []
        problematic_symbols = []
        # Проверяем кэш в Redis
        valid_symbols_key = f"valid_symbols:{user or 'unknown'}"
        problematic_symbols_key = f"problematic_symbols:{user or 'unknown'}"
        cached_valid = await redis_client.get(valid_symbols_key)
        cached_problematic = await redis_client.get(problematic_symbols_key)

        if cached_valid and cached_problematic:
            valid_symbols = json.loads(cached_valid.decode())
            problematic_symbols = json.loads(cached_problematic.decode())
            logger.info(f"Loaded {len(valid_symbols)} valid symbols and {len(problematic_symbols)} problematic symbols from Redis cache")
            return valid_symbols

        # Фильтруем символы, которые ещё не в кэше
        symbols_to_filter = [s for s in symbols if s not in problematic_symbols]
        for i in range(0, len(symbols_to_filter), batch_size):
            batch = symbols_to_filter[i:i + batch_size]
            for symbol in batch:
                if not symbol.endswith('/USDT'):
                    problematic_symbols.append(symbol)
                    continue
                try:
                    ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
                    logger.debug(f"Fetched {len(ohlcv)} candles for {symbol}")
                    if len(ohlcv) < limit:
                        logger.warning(f"Skipping {symbol}: insufficient data (only {len(ohlcv)} candles)")
                        problematic_symbols.append(symbol)
                        continue
                    volume = sum(candle[5] for candle in ohlcv)
                    if volume == 0:
                        logger.warning(f"Skipping {symbol}: zero trading volume")
                        problematic_symbols.append(symbol)
                        continue
                    valid_symbols.append(symbol)
                except Exception as e:
                    if "429" in str(e):
                        logger.warning(f"Rate limit exceeded for {symbol}, pausing for 5 seconds...")
                        await asyncio.sleep(5)
                        continue
                    logger.error(f"Failed to fetch OHLCV for {symbol}: {type(e).__name__}: {str(e)}")
                    problematic_symbols.append(symbol)
                    continue
                # Добавляем задержку 0.5 секунды между запросами
                await asyncio.sleep(0.5)
            logger.info(f"Processed batch {i//batch_size + 1} of {len(symbols_to_filter)//batch_size + 1}, found {len(valid_symbols)} valid symbols so far")

        # Сохраняем результаты в Redis
        await redis_client.set(valid_symbols_key, json.dumps(valid_symbols), ex=86400)  # Кэшируем на 24 часа
        await redis_client.set(problematic_symbols_key, json.dumps(problematic_symbols), ex=86400)
        logger.info(f"Cached {len(valid_symbols)} valid symbols and {len(problematic_symbols)} problematic symbols in Redis")

        logger.info(f"Filtered {len(valid_symbols)} valid symbols for user {user or 'unknown'} in {market_state or 'unknown'} market state")
        return valid_symbols
    except Exception as e:
        logger.error(f"Failed to filter symbols: {type(e).__name__}: {str(e)}")
        return []
    finally:
        await redis_client.close()
