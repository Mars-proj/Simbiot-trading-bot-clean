import asyncio
import json
import time
from logging_setup import logger_main

async def get_test_symbols(exchange_pool, exchange_id, user_id, testnet=False):
    """Fetches and filters tradable symbols from the exchange."""
    logger_main.info(f"Fetching tradable symbols for {exchange_id} for user {user_id}")
    try:
        # Get exchange instance
        exchange = await exchange_pool.get_exchange(exchange_id, user_id, testnet)
        if not exchange:
            logger_main.error(f"Failed to get exchange instance for {exchange_id}:{user_id}")
            return []

        # Fetch all markets from the exchange
        markets = await exchange.fetch_markets()
        logger_main.info(f"Fetched {len(markets)} markets from {exchange_id}")

        # Filter tradable symbols
        tradable_symbols = []
        for market in markets:
            symbol = market.get('symbol')
            if not symbol:
                continue
            # Check if the symbol is active and tradable
            if not market.get('active', False):
                logger_main.debug(f"Symbol {symbol} is not active, skipping")
                continue
            # Check if spot trading is enabled (for MEXC, we focus on spot)
            if market.get('spot', False) and market.get('quote') == 'USDT':
                # Fetch ticker to check trading volume
                try:
                    ticker = await exchange.fetch_ticker(symbol)
                    volume = ticker.get('baseVolume', 0)
                    if volume > 0:  # Ensure there is trading activity
                        tradable_symbols.append(symbol)
                        logger_main.debug(f"Added tradable symbol {symbol} with volume {volume}")
                    else:
                        logger_main.debug(f"Symbol {symbol} has no trading volume, skipping")
                except Exception as e:
                    logger_main.warning(f"Failed to fetch ticker for {symbol}: {e}")
                    continue

        logger_main.info(f"Found {len(tradable_symbols)} tradable symbols: {tradable_symbols[:5]}...")

        # Close the exchange instance if it was created here
        if not exchange_pool.exchanges.get(f"{exchange_id}:{user_id}"):
            await exchange_pool.close_exchange(exchange_id, user_id)

        return tradable_symbols

    except Exception as e:
        logger_main.error(f"Error fetching test symbols: {e}")
        return []
