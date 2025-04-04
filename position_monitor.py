# position_monitor.py
import asyncio
from logging_setup import logger_main
from trade_pool_core import fetch_positions

async def monitor_positions(exchange_id, user_id, exchange, testnet=False):
    """
    Monitors open positions for the user on the given exchange.
    Args:
        exchange_id (str): Exchange identifier (e.g., 'mexc')
        user_id (str): User identifier
        exchange: Exchange instance from ccxt
        testnet (bool): Whether to use testnet
    """
    try:
        # Временно отключаем запрос позиций для user2 из-за проблемы с правами API
        if user_id == "user2":
            logger_main.info(f"Skipping position monitoring for user {user_id} on {exchange_id} due to API permission issue")
            return

        logger_main.info(f"Monitoring positions for user {user_id} on {exchange_id}")
        positions = await fetch_positions(exchange_id, user_id, exchange, testnet)
        if not positions:
            logger_main.info(f"No open positions for user {user_id} on {exchange_id}")
            return

        logger_main.info(f"Found {len(positions)} open positions for user {user_id} on {exchange_id}: {positions}")
        # Здесь можно добавить логику для управления позициями (например, закрытие убыточных позиций)
    except Exception as e:
        logger_main.error(f"Error monitoring positions for user {user_id} on {exchange_id}: {e}")
