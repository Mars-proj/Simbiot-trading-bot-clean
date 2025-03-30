import ccxt.async_support as ccxt
from logging_setup import logger_main

async def fetch_ticker(exchange, symbol):
    """Fetches ticker data for a given symbol from an exchange."""
    try:
        # Validate exchange
        if not isinstance(exchange, ccxt.async_support.BaseExchange):
            logger_main.error(f"Invalid exchange object: must be a ccxt.async_support.BaseExchange instance")
            return None

        ticker = await exchange.fetch_ticker(symbol)
        if not ticker:
            logger_main.error(f"Failed to fetch ticker for {symbol} on {exchange.id}")
            return None

        bid = ticker.get('bid', 'N/A')
        ask = ticker.get('ask', 'N/A')
        logger_main.info(f"Fetched ticker for {symbol} on {exchange.id}: bid={bid}, ask={ask}")
        return ticker
    except Exception as e:
        logger_main.error(f"Error fetching ticker for {symbol} on {exchange.id}: {e}")
        return None

async def fetch_order_book(exchange, symbol):
    """Fetches order book data for a given symbol from an exchange."""
    try:
        # Validate exchange
        if not isinstance(exchange, ccxt.async_support.BaseExchange):
            logger_main.error(f"Invalid exchange object: must be a ccxt.async_support.BaseExchange instance")
            return None

        order_book = await exchange.fetch_order_book(symbol)
        if not order_book:
            logger_main.error(f"Failed to fetch order book for {symbol} on {exchange.id}")
            return None

        bid = order_book['bids'][0][0] if order_book['bids'] else 'N/A'
        ask = order_book['asks'][0][0] if order_book['asks'] else 'N/A'
        logger_main.info(f"Fetched order book for {symbol} on {exchange.id}: top bid={bid}, top ask={ask}")
        return order_book
    except Exception as e:
        logger_main.error(f"Error fetching order book for {symbol} on {exchange.id}: {e}")
        return None

__all__ = ['fetch_ticker', 'fetch_order_book']
