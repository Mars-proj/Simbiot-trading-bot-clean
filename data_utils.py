from utils import logger_main, logger_debug, log_exception
import asyncio
import pandas as pd
import ccxt.async_support as ccxt
import redis.asyncio as redis
import json
import time

async def fetch_and_prepare_ohlcv(exchange, symbol, timeframe="1h", limit=72):
    try:
        # Подключение к Redis
        redis_client = redis.Redis(host='localhost', port=6379, db=0)
        
        # Ключ для хранения OHLCV в Redis
        cache_key = f"ohlcv:{exchange.id}:{symbol}:{timeframe}"
        
        # Проверяем, есть ли данные в кэше
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            ohlcv_data = json.loads(cached_data)
            df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            logger_main.debug(f"OHLCV для {symbol} загружен из кэша: строк={len(df)}")
        else:
            # Загружаем данные с биржи
            logger_main.debug(f"OHLCV загружен для {symbol} с {timeframe}, строк: {limit}")
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            if not ohlcv or len(ohlcv) < limit:
                logger_main.warning(f"Недостаточно данных OHLCV для {symbol}, получено {len(ohlcv)} строк")
                await redis_client.close()
                return None
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Конвертируем timestamp в строку для JSON-сериализации
            df_for_cache = df.copy()
            df_for_cache['timestamp'] = df_for_cache['timestamp'].astype(str)
            
            # Сохраняем в кэш с TTL 1 час
            ohlcv_json = df_for_cache.to_dict(orient='records')
            await redis_client.setex(cache_key, 3600, json.dumps(ohlcv_json))
            logger_main.debug(f"OHLCV для {symbol} сохранён в кэш")

        # Добавляем технические индикаторы
        df['returns'] = df['close'].pct_change()
        df['ma_short'] = df['close'].rolling(window=10).mean()
        df['ma_long'] = df['close'].rolling(window=20).mean()
        df['bb_upper'] = df['close'].rolling(window=20).mean() + 2 * df['close'].rolling(window=20).std()
        df['bb_lower'] = df['close'].rolling(window=20).mean() - 2 * df['close'].rolling(window=20).std()
        logger_main.debug(f"OHLCV для {symbol}: строк={len(df)}, колонки={df.columns.tolist()}")
        
        await redis_client.close()
        return df
    except Exception as e:
        log_exception(f"Ошибка загрузки OHLCV для {symbol}", e)
        await redis_client.close()
        return None
