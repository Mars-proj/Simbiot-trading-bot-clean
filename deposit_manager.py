import asyncio
import time
from logging_setup import logger_main
from utils import log_exception
from global_objects import redis_client, global_trade_pool

class DepositManager:
    def __init__(self, cache_timeout=300):
        self.cache_timeout = cache_timeout  # Cache lifetime in seconds (5 minutes)

    async def initialize_deposit(self, exchange, user_id, risk_manager):
        """Initializes the deposit for a user"""
        logger_main.info(f"Initializing deposit for user {user_id}")
        try:
            total_deposit = await self.calculate_total_deposit(exchange, user_id)
            risk_manager.set_initial_deposit(total_deposit)
            logger_main.info(f"Deposit initialized for {user_id}: {total_deposit} USDT")
        except Exception as e:
            logger_main.error(f"Error initializing deposit for {user_id}: {str(e)}")
            log_exception(f"Error initializing deposit: {str(e)}", e)

    async def calculate_total_deposit(self, exchange, user_id):
        """Calculates the total deposit for a user"""
        logger_main.info(f"Calculating deposit for user {user_id}")
        try:
            balance = await self.get_balance(exchange, user_id, force_refresh=True)
            total_deposit = balance.get('USDT', {}).get('total', 0)
            logger_main.info(f"Total deposit for {user_id}: {total_deposit} USDT")
            return total_deposit
        except Exception as e:
            logger_main.error(f"Error calculating deposit for {user_id}: {str(e)}")
            log_exception(f"Error calculating deposit: {str(e)}", e)
            return 0

    async def get_balance(self, exchange, user_id, force_refresh=False):
        """Fetches the balance for a user, with caching in Redis"""
        logger_main.info(f"Checking balance cache for user {user_id}, force_refresh={force_refresh}")
        current_time = time.time()
        cache_key = f"balance:{user_id}"
        if not force_refresh:
            cached_balance = await redis_client.get_json(cache_key)
            if cached_balance:
                logger_main.info(f"Using cached balance for {user_id}")
                return cached_balance
        logger_main.info(f"Fetching balance (async) for user {user_id}, attempt 1/3")
        for attempt in range(3):
            try:
                balance = await exchange.fetch_balance()
                logger_main.info(f"Full balance response for {user_id}: {balance}")
                if balance is None:
                    raise Exception("Failed to fetch balance")
                if 'USDT' not in balance:
                    logger_main.warning(f"No USDT in balance for {user_id}, available currencies: {list(balance.keys())}")
                    return {'USDT': {'free': 0, 'used': 0, 'total': 0}}
                logger_main.info(f"USDT balance for {user_id}: free={balance['USDT']['free']}, used={balance['USDT']['used']}, total={balance['USDT']['total']}")
                # Cache in Redis for cache_timeout seconds
                await redis_client.set_json(cache_key, balance, expire=self.cache_timeout)
                # Update available tokens in trade_pool
                if 'free' in balance:
                    available_tokens = {asset: amount for asset, amount in balance['free'].items() if isinstance(amount, (int, float)) and amount > 0}
                else:
                    available_tokens = {}
                    for asset, data in balance.items():
                        if isinstance(data, dict) and 'free' in data and isinstance(data['free'], (int, float)) and data['free'] > 0:
                            available_tokens[asset] = data['free']
                logger_main.debug(f"Available tokens for {user_id}: {available_tokens}")
                await global_trade_pool.update_available_tokens(user_id, available_tokens)
                return balance
            except Exception as e:
                logger_main.warning(f"Error fetching balance for {user_id}, attempt {attempt + 1}/3: {str(e)}")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                else:
                    logger_main.error(f"Failed to fetch balance for {user_id} after 3 attempts: {str(e)}")
                    log_exception(f"Failed to fetch balance: {str(e)}", e)
                    return {'USDT': {'free': 0, 'used': 0, 'total': 0}}

__all__ = ['DepositManager']
