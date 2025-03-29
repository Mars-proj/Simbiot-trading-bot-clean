import ccxt.async_support as ccxt
import time
from logging_setup import logger_main, logger_exceptions
from redis_initializer import redis_client
from redis_client import get_json, set_json  # Импортируем функции напрямую

class DepositCalculator:
    def __init__(self, user_id=None, max_drawdown=0.1):
        self.user_id = user_id
        self.total_deposit_usdt = 0.0
        self.max_drawdown = max_drawdown  # Максимальная просадка (например, 0.1 = 10%)
        self.balance_cache_key = f"deposit:{self.user_id}" if self.user_id else None
        self.time_offset = 0  # Смещение времени для синхронизации с сервером MEXC

    async def sync_time_with_mexc(self, exchange):
        """Синхронизирует время с сервером MEXC"""
        try:
            logger_main.debug("Attempting to fetch server time from MEXC")
            response = await exchange.fetch_time()
            server_time = response  # Время сервера в миллисекундах
            local_time = int(time.time() * 1000)  # Локальное время в миллисекундах
            self.time_offset = server_time - local_time
            logger_main.info(f"Synchronized time with MEXC: server_time={server_time}, local_time={local_time}, offset={self.time_offset} ms")
        except Exception as e:
            logger_main.error(f"Failed to sync time with MEXC: {str(e)}")
            logger_exceptions.error(f"Time sync error: {str(e)}", exc_info=True)

    async def fetch_price(self, exchange, asset, target_currency="USDT"):
        """Получает цену актива в USDT, используя промежуточные пары, если нужно"""
        start_time = time.time()
        # Проверяем кэш цены
        price_cache_key = f"price:{asset}/{target_currency}"
        cached_price = await get_json(price_cache_key)
        if cached_price is not None:
            logger_main.debug(f"Using cached price for {asset}/{target_currency}: {cached_price}")
            return cached_price
        try:
            # Прямой тикер (например, BTC/USDT)
            ticker = await exchange.fetch_ticker(f"{asset}/{target_currency}")
            price = ticker['last'] if ticker and 'last' in ticker else 0
            logger_main.debug(f"Fetched price for {asset}/{target_currency}: {price}")
            if price > 0:
                await set_json(price_cache_key, price, expire=300)  # Кэшируем на 5 минут
            return price
        except Exception as e:
            logger_main.warning(f"Cannot fetch price for {asset}/{target_currency}: {str(e)}")
            # Пробуем через промежуточные пары (например, через BTC или ETH)
            intermediate_currencies = ['BTC', 'ETH']
            for intermediate in intermediate_currencies:
                try:
                    # Получаем цену актива в промежуточной валюте (например, ASSET/BTC)
                    ticker1 = await exchange.fetch_ticker(f"{asset}/{intermediate}")
                    price_in_intermediate = ticker1['last'] if ticker1 and 'last' in ticker1 else 0
                    logger_main.debug(f"Fetched price for {asset}/{intermediate}: {price_in_intermediate}")
                    if price_in_intermediate == 0:
                        continue
                    # Получаем цену промежуточной валюты в USDT (например, BTC/USDT)
                    ticker2 = await exchange.fetch_ticker(f"{intermediate}/{target_currency}")
                    price_intermediate_to_usdt = ticker2['last'] if ticker2 and 'last' in ticker2 else 0
                    logger_main.debug(f"Fetched price for {intermediate}/{target_currency}: {price_intermediate_to_usdt}")
                    if price_intermediate_to_usdt == 0:
                        continue
                    price = price_in_intermediate * price_intermediate_to_usdt
                    if price > 0:
                        await set_json(price_cache_key, price, expire=300)  # Кэшируем на 5 минут
                    return price
                except Exception as e:
                    logger_main.warning(f"Cannot fetch price for {asset} via {intermediate}: {str(e)}")
            return 0
        finally:
            logger_main.debug(f"fetch_price for {asset}/{target_currency} took {time.time() - start_time:.3f} seconds")

    async def calculate_total_deposit(self, exchange):
        """Рассчитывает общий депозит в USDT, кэширует его в Redis"""
        # Проверяем кэш
        if self.balance_cache_key:
            cached_deposit = await get_json(self.balance_cache_key)
            if cached_deposit is not None:
                self.total_deposit_usdt = cached_deposit
                logger_main.info(f"Using cached deposit for user {self.user_id}: {self.total_deposit_usdt} USDT")
                return
        try:
            # Отключаем проверку времени для MEXC
            exchange.options['enableTimeSync'] = False
            # Устанавливаем recvWindow для MEXC
            exchange.options['recvWindow'] = 30000  # 30 секунд
            # Логируем время перед запросом
            request_time = int(time.time() * 1000)  # Время в миллисекундах
            logger_main.debug(f"Sending request to MEXC with timestamp: {request_time}")
            # Проверяем права API
            try:
                account_info = await exchange.fetch_balance()
                logger_main.debug(f"Account info for user {self.user_id}: {account_info}")
            except Exception as e:
                logger_main.error(f"Failed to fetch account info, possible API key permission issue for user {self.user_id}: {str(e)}")
                logger_exceptions.error(f"API key permission issue: {str(e)}", exc_info=True)
                return
            balance = await exchange.fetch_balance()
            logger_main.debug(f"Fetched balance for user {self.user_id}: {balance}")
            total_deposit_usdt = 0.0
            # Проверяем, есть ли поле 'total' или 'info'
            if 'total' in balance:
                balance_data = balance['total']
            elif 'info' in balance and isinstance(balance['info'], dict):
                balance_data = balance['info']
            else:
                balance_data = balance
            for asset, amount in balance_data.items():
                logger_main.debug(f"Processing asset {asset}: {amount}")
                total = 0.0
                if isinstance(amount, dict):
                    free = float(amount.get('free', 0.0)) if amount.get('free') else 0.0
                    locked = float(amount.get('locked', 0.0)) if amount.get('locked') else 0.0
                    total = free + locked
                else:
                    total = float(amount) if amount else 0.0
                logger_main.debug(f"Asset {asset}: total={total}")
                if total <= 0:
                    continue
                if asset == 'USDT':
                    total_deposit_usdt += total
                else:
                    price = await self.fetch_price(exchange, asset, "USDT")
                    if price > 0:
                        total_deposit_usdt += total * price
                        logger_main.debug(f"Converted {total} {asset} to {total * price} USDT (price: {price})")
                    else:
                        logger_main.warning(f"Could not determine price for {asset}, skipping in deposit calculation")
            self.total_deposit_usdt = total_deposit_usdt
            logger_main.info(f"Deposit initialized for user {self.user_id}: {self.total_deposit_usdt} USDT")
            # Кэшируем депозит в Redis на 5 минут
            if self.balance_cache_key:
                await set_json(self.balance_cache_key, self.total_deposit_usdt, expire=300)
        except Exception as e:
            logger_main.error(f"Error calculating deposit for user {self.user_id}: {str(e)}")
            logger_exceptions.error(f"Error calculating deposit: {str(e)}", exc_info=True)

    async def update_deposit(self, exchange):
        """Обновляет депозит после каждой операции"""
        await self.calculate_total_deposit(exchange)

    def check_drawdown(self, exchange):
        if self.user_id is None:
            logger_main.warning("Total deposit is 0 for user None, cannot calculate drawdown")
            return False
        if self.total_deposit_usdt <= 0:
            logger_main.warning(f"Total deposit is 0 for user {self.user_id}, cannot calculate drawdown")
            return False
        # Здесь можно добавить логику проверки просадки, если есть данные о PNL
        # Для простоты пока просто проверяем, что депозит больше минимального
        return True

__all__ = ['DepositCalculator']
