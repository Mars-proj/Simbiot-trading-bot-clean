# market_state_analyzer.py
import logging
import asyncio
import aiohttp
import json
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
        return {'trend': 'neutral', 'volatility': 0.01}, []

    # Получаем кэшированные символы
    available_symbols, problematic_symbols = await get_cached_symbols()
    new_available_symbols = []
    new_problematic_symbols = []

    try:
        logger.debug("Fetching markets from MEXC API")
        markets = await asyncio.wait_for(exchange.fetch_markets(), timeout=60)
        logger.info(f"Fetched {len(markets)} markets")
        # Сохраняем данные fetch_markets в файл для отладки
        with open("/root/trading_bot/fetch_markets_data.json", "w") as f:
            json.dump(markets, f, indent=2)
        logger.info(f"Saved fetch_markets data to /root/trading_bot/fetch_markets_data.json")
        logger.info(f"First 5 markets: {markets[:5]}")

        # Считаем статистику для отладки
        usdt_symbols = 0
        enabled_symbols = 0
        active_symbols = 0
        quote_values = set()
        market_types = set()

        # Фильтруем активные символы
        total_change = 0.0
        count = 0
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
                # Используем данные из fetch_markets для анализа
                if 'info' in market and 'change' in market['info']:
                    try:
                        price_change = float(market['info']['change'])
                        total_change += price_change
                        count += 1
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid change data for {symbol}: {e}")
                        new_problematic_symbols.append(symbol)
                        new_available_symbols.remove(symbol)
                        continue
            else:
                new_problematic_symbols.append(symbol)
                logger.warning(f"Symbol {symbol} is inactive, added to problematic symbols")

        logger.info(f"Statistics: USDT symbols={usdt_symbols}, enabled symbols={enabled_symbols}, active symbols={active_symbols}")
        logger.info(f"Unique quote values: {list(quote_values)}")
        logger.info(f"Unique market types: {list(market_types)}")

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
        return market_state, new_available_symbols

    except asyncio.TimeoutError as te:
        logger.error(f"Timeout while fetching markets: {te}")
        return {'trend': 'neutral', 'volatility': 0.01}, []
    except Exception as e:
        logger.error(f"Failed to fetch markets: {type(e).__name__}: {str(e)}")
        return {'trend': 'neutral', 'volatility': 0.01}, []
