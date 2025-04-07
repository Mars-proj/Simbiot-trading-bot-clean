import logging
import asyncio
import aiohttp
from symbol_filter import get_cached_symbols, cache_symbols

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
    new_problematic_symbols = []

    for symbol in symbols_to_try:
        if symbol in problematic_symbols:
            logger.warning(f"Skipping {symbol} as it is in problematic symbols")
            continue

        try:
            logger.debug(f"Fetching ticker for {symbol} (attempt 1/1)")
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
            
            # Обновляем кэш, если есть новые проблемные символы
            if new_problematic_symbols:
                await cache_symbols(available_symbols, list(set(problematic_symbols + new_problematic_symbols)))
            return market_state
        except asyncio.TimeoutError as te:
            logger.error(f"Timeout while fetching ticker for {symbol}: {te}")
            new_problematic_symbols.append(symbol)
            logger.warning(f"Added {symbol} to problematic symbols due to timeout")
        except Exception as e:
            logger.error(f"Failed to fetch ticker for {symbol}: {type(e).__name__}: {str(e)}")
            new_problematic_symbols.append(symbol)
            logger.warning(f"Added {symbol} to problematic symbols due to error")
    
    logger.error("Failed to fetch ticker for all attempted symbols, returning default market state")
    # Обновляем кэш с новыми проблемными символами
    if new_problematic_symbols:
        await cache_symbols(available_symbols, list(set(problematic_symbols + new_problematic_symbols)))
    return {'trend': 'neutral', 'volatility': 0.01}
