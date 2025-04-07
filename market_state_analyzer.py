import logging
import asyncio
import aiohttp
from symbol_filter import get_cached_symbols

logger = logging.getLogger("main")

async def check_network_access():
    """Проверяет доступность API MEXC перед выполнением запросов."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.mexc.com/api/v3/ping', timeout=5) as response:
                if response.status == 200:
                    logger.info("Network access to MEXC API confirmed")
                    return True
                else:
                    logger.error(f"MEXC API ping failed with status: {response.status}")
                    return False
    except Exception as e:
        logger.error(f"Failed to ping MEXC API: {type(e).__name__}: {str(e)}")
        return False

async def analyze_market_state(exchange, timeframe='1h'):
    logger.info(f"Analyzing market state with timeframe {timeframe}")
    
    # Проверяем доступность API перед запросом
    if not await check_network_access():
        logger.error("MEXC API is not accessible, returning default market state")
        return {'trend': 'neutral', 'volatility': 0.01}

    # Получаем кэшированные символы
    available_symbols, problematic_symbols = await get_cached_symbols()
    symbols_to_try = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']  # Список символов для анализа

    retry_count = 3
    for symbol in symbols_to_try:
        if symbol in problematic_symbols:
            logger.warning(f"Skipping {symbol} as it is in problematic symbols")
            continue

        for attempt in range(retry_count):
            try:
                logger.debug(f"Fetching ticker for {symbol} (attempt {attempt + 1}/{retry_count})")
                ticker = await asyncio.wait_for(
                    exchange.fetch_ticker(symbol),
                    timeout=20
                )
                logger.debug(f"Ticker data for {symbol}: {ticker}")
                price_change = ticker['percentage']  # Процент изменения цены за 24 часа
                
                # Простой пример определения тренда
                trend = 'bullish' if price_change > 0 else 'bearish'
                
                # Пример: Оценка волатильности
                volatility = abs(price_change) / 100

                market_state = {
                    'trend': trend,
                    'volatility': volatility,
                }
                logger.info(f"Market state analyzed using {symbol}: {market_state}")
                return market_state
            except asyncio.TimeoutError as te:
                logger.error(f"Timeout while fetching ticker for {symbol} on attempt {attempt + 1}/{retry_count}: {te}")
                if attempt < retry_count - 1:
                    logger.info(f"Retrying in 10 seconds...")
                    await asyncio.sleep(10)
                else:
                    logger.error(f"Failed to fetch ticker for {symbol} after all retries due to timeout")
            except Exception as e:
                logger.error(f"Failed to fetch ticker for {symbol} on attempt {attempt + 1}/{retry_count}: {type(e).__name__}: {str(e)}")
                if attempt < retry_count - 1:
                    logger.info(f"Retrying in 10 seconds...")
                    await asyncio.sleep(10)
                else:
                    logger.error(f"Failed to fetch ticker for {symbol} after all retries")
    
    logger.error("Failed to fetch ticker for all attempted symbols, returning default market state")
    return {'trend': 'neutral', 'volatility': 0.01}
