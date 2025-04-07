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
    new_available_symbols = []
    new_problematic_symbols = []

    try:
        logger.debug("Fetching markets from MEXC API")
        markets = await asyncio.wait_for(exchange.fetch_markets(), timeout=60)  # Увеличиваем таймаут до 60 секунд
        logger.debug(f"Fetched {len(markets)} markets")

        # Фильтруем активные символы
        total_change = 0.0
        count = 0
        for market in markets:
            symbol = market['symbol']
            if market.get('active', False):
                new_available_symbols.append(symbol)
                # Используем данные из fetch_markets для анализа
                if 'info' in market and 'change' in market['info']:
                    try:
                        price_change = float(market['info']['change'])
                        total_change += price_change
                        count += 1
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid change data for {symbol}: {e}")
                        new_problematic_symbols.append(symbol)
                        continue
            else:
                new_problematic_symbols.append(symbol)
                logger.warning(f"Symbol {symbol} is inactive, added to problematic symbols")

        # Обновляем кэш символов
        await cache_symbols(new_available_symbols, new_problematic_symbols)

        # Анализируем состояние рынка на основе данных из fetch_markets
        if count > 0:
            avg_change = total_change / count
            trend = 'bullish' if avg_change > 0 else 'bearish'
            volatility = abs(avg_change) / 100
        else:
            logger.error("No valid symbols for market state analysis, returning default market state")
            trend = 'neutral'
            volatility = 0.01

        market_state = {
            'trend': trend,
            'volatility': volatility,
        }
        logger.info(f"Market state analyzed: {market_state}")
        return market_state

    except asyncio.TimeoutError as te:
        logger.error(f"Timeout while fetching markets: {te}")
        return {'trend': 'neutral', 'volatility': 0.01}
    except Exception as e:
        logger.error(f"Failed to fetch markets: {type(e).__name__}: {str(e)}")
        return {'trend': 'neutral', 'volatility': 0.01}
