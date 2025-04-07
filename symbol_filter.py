# symbol_filter.py
import logging
import asyncio
import json
from historical_data_fetcher import fetch_historical_data
import redis.asyncio as redis

logger = logging.getLogger("main")

async def get_redis_client():
    """Инициализация Redis клиента."""
    return await redis.from_url("redis://localhost:6379/0")

async def cache_symbols(available_symbols, problematic_symbols):
    """Кэширует доступные и проблемные символы в Redis с TTL 24 часа."""
    redis_client = await get_redis_client()
    try:
        # Сохраняем доступные символы
        await redis_client.set("available_symbols", ",".join(available_symbols), ex=86400)
        # Сохраняем проблемные символы
        await redis_client.set("problematic_symbols", ",".join(problematic_symbols), ex=86400)
        logger.info(f"Cached {len(available_symbols)} available symbols and {len(problematic_symbols)} problematic symbols in Redis")
    finally:
        await redis_client.close()

async def get_cached_symbols():
    """Получает кэшированные символы из Redis."""
    redis_client = await get_redis_client()
    try:
        available = await redis_client.get("available_symbols")
        problematic = await redis_client.get("problematic_symbols")
        available_symbols = available.decode().split(",") if available else []
        problematic_symbols = problematic.decode().split(",") if problematic else []
        return available_symbols, problematic_symbols
    finally:
        await redis_client.close()

async def filter_symbols(exchange, symbols, since, limit, timeframe, user, market_state):
    logger.info(f"Starting symbol filtering for {len(symbols)} symbols with market state {market_state}")

    # Проверяем, есть ли кэшированные символы
    available_symbols, problematic_symbols = await get_cached_symbols()
    
    if available_symbols and problematic_symbols:
        logger.info("Using cached symbols from Redis")
        valid_symbols = [symbol for symbol in symbols if symbol in available_symbols]
    else:
        # Если кэша нет, получаем данные через fetch_markets
        try:
            logger.debug("Fetching markets from MEXC API for symbol filtering")
            markets = await asyncio.wait_for(exchange.fetch_markets(), timeout=30)
            logger.info(f"Fetched {len(markets)} markets")
            # Сохраняем данные fetch_markets в файл для отладки
            with open("/root/trading_bot/fetch_markets_data_symbol_filter.json", "w") as f:
                json.dump(markets, f, indent=2)
            logger.info(f"Saved fetch_markets data to /root/trading_bot/fetch_markets_data_symbol_filter.json")
            logger.info(f"First 5 markets: {markets[:5]}")

            # Считаем статистику для отладки
            usdt_symbols = 0
            enabled_symbols = 0
            active_symbols = 0
            quote_values = set()
            market_types = set()

            new_available_symbols = []
            new_problematic_symbols = []
            for market in markets:
                symbol = market['symbol']
                quote = market.get('quote', '')
                market_type = market.get('type', 'unknown')
                quote_values.add(quote)
                market_types.add(market_type)
                # Проверяем, что это спотовый рынок
                is_spot = market_type == 'spot'
                # Считаем статистику
                if quote.upper().endswith('USDT'):
                    usdt_symbols += 1
                if market.get('info', {}).get('state', 'enabled') != '0':
                    enabled_symbols += 1
                if market.get('active', False):
                    active_symbols += 1

                # Проверяем, активен ли символ
                is_active = (is_spot and quote.upper().endswith('USDT') and market.get('active', False))
                logger.info(f"Symbol {symbol}: active={market.get('active')}, state={market.get('info', {}).get('state')}, quote={quote}, type={market_type}, is_active={is_active}")
                if is_active:
                    new_available_symbols.append(symbol)
                else:
                    new_problematic_symbols.append(symbol)
                    logger.warning(f"Symbol {symbol} is inactive, added to problematic symbols")

            logger.info(f"Statistics: USDT symbols={usdt_symbols}, enabled symbols={enabled_symbols}, active symbols={active_symbols}")
            logger.info(f"Unique quote values: {list(quote_values)}")
            logger.info(f"Unique market types: {list(market_types)}")

            # Обновляем кэш
            await cache_symbols(new_available_symbols, new_problematic_symbols)
            valid_symbols = [symbol for symbol in symbols if symbol in new_available_symbols]
            available_symbols = new_available_symbols
            problematic_symbols = new_problematic_symbols
        except Exception as e:
            logger.error(f"Failed to fetch markets: {type(e).__name__}: {str(e)}")
            valid_symbols = []
            available_symbols = []
            problematic_symbols = symbols  # Считаем все символы проблемными

    # Фильтруем символы по историческим данным
    final_valid_symbols = []
    batch_size = 10
    batches = [valid_symbols[i:i + batch_size] for i in range(0, len(valid_symbols), batch_size)]

    # Пример: Используем market_state для фильтрации
    min_data_points = 89 if market_state.get('trend') == 'bullish' else 50

    for batch_idx, batch in enumerate(batches):
        logger.info(f"Fetching historical data for batch {batch_idx + 1} of {len(batches)}")
        tasks = []
        for symbol in batch:
            logger.debug(f"Queuing fetch for {symbol}")
            tasks.append(fetch_historical_data(symbol, exchange, since, limit, timeframe, user))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for symbol, result in zip(batch, results):
            if isinstance(result, Exception):
                logger.warning(f"Moved {symbol} from working to problematic symbols: {result}")
                problematic_symbols.append(symbol)
                if symbol in available_symbols:
                    available_symbols.remove(symbol)
            elif result and len(result) >= min_data_points:
                logger.info(f"Fetched {len(result)} OHLCV data points for {symbol}")
                final_valid_symbols.append(symbol)
            else:
                logger.warning(f"Insufficient data for {symbol}: {len(result)} OHLCV points")
                problematic_symbols.append(symbol)
                if symbol in available_symbols:
                    available_symbols.remove(symbol)

    # Обновляем кэш с учётом новых проблемных символов
    await cache_symbols(available_symbols, problematic_symbols)

    logger.info(f"Filtered {len(final_valid_symbols)} valid symbols out of {len(symbols)}")
    return final_valid_symbols
