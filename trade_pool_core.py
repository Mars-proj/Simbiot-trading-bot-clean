# trade_pool_core.py
import asyncio
from logging_setup import logger_main

async def fetch_positions(exchange_id, user_id, exchange, testnet=False):
    """
    Fetches open positions for the user on the given exchange.
    Args:
        exchange_id (str): Exchange identifier (e.g., 'mexc')
        user_id (str): User identifier
        exchange: Exchange instance from ccxt
        testnet (bool): Whether to use testnet
    Returns:
        list: List of open positions
    """
    try:
        logger_main.info(f"Fetching positions for user {user_id} on {exchange_id}")
        # Запрашиваем открытые позиции через API биржи
        positions = await exchange.fetch_positions()
        logger_main.info(f"Fetched {len(positions)} positions for user {user_id} on {exchange_id}")
        return positions
    except Exception as e:
        logger_main.error(f"Error fetching positions for {exchange_id}:{user_id}: {exchange_id} {str(e)}")
        return []
