import asyncio
from logging_setup import logger_main, logger_exceptions
from redis_client import redis_client, get_problematic_symbols

async def filter_symbols(exchange):
    """Фильтрует символы для торговли"""
    try:
        # Получаем кэшированные проблемные символы
        problematic_symbols = await get_problematic_symbols(exchange.id)
        logger_main.debug(f"Problematic symbols for {exchange.id}: {problematic_symbols}")

        # Получаем все рынки
        markets = await exchange.load_markets()
        symbols = list(markets.keys())
        logger_main.debug(f"Total symbols loaded: {len(symbols)}")

        # Фильтруем только спотовые рынки с USDT
        tradable_symbols = []
        for symbol in symbols:
            if '/USDT' in symbol and markets[symbol].get('spot', False):
                # Проверяем, не является ли символ проблемным
                if symbol not in problematic_symbols:
                    tradable_symbols.append(symbol)

        logger_main.info(f"Filtered symbols: {len(tradable_symbols)}")
        return tradable_symbols
    except Exception as e:
        logger_main.error(f"Error filtering symbols: {str(e)}")
        logger_exceptions.error(f"Error filtering symbols: {str(e)}", exc_info=True)
        return []

__all__ = ['filter_symbols']
