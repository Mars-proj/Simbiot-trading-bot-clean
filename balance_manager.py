import ccxt.async_support as ccxt  # Используем асинхронный клиент ccxt
import asyncio
import time
from logging_setup import logger_main
from utils import log_exception

class BalanceManager:
    def __init__(self):
        # Кэш баланса уникален для каждого пользователя
        self.balance_cache = {}  # {user_id: {'balance': balance, 'timestamp': timestamp}}
        self.cache_duration = 30  # Кэшировать баланс на 30 секунд
        self.suspended_users = {}  # Пользователи, для которых торговля приостановлена
        self.suspension_duration = 300  # Приостановка на 5 минут
        # Сбрасываем кэш при инициализации
        logger_main.debug("Сбрасываем кэш баланса при инициализации")
        self.balance_cache.clear()

    async def fetch_balance_with_cache(self, exchange, user_id, force_refresh=False):
        """Получение баланса с кэшированием (асинхронный вызов)"""
        # Проверяем, не приостановлена ли торговля для пользователя
        current_time = time.time()
        if user_id in self.suspended_users:
            suspension_end = self.suspended_users[user_id]
            if current_time < suspension_end:
                logger_main.warning(f"Торговля для пользователя {user_id} приостановлена до {suspension_end}, пропускаем")
                return None
            else:
                logger_main.info(f"Возобновляем торговлю для пользователя {user_id}")
                del self.suspended_users[user_id]
        # Добавляем отладку для проверки кэша
        logger_main.debug(f"Проверка кэша для пользователя {user_id}, force_refresh={force_refresh}")
        if user_id in self.balance_cache:
            cache_entry = self.balance_cache[user_id]
            logger_main.debug(f"Кэш для {user_id}: {cache_entry['balance']}, возраст кэша: {current_time - cache_entry['timestamp']} секунд")
        # Временно отключаем кэширование для отладки
        # if not force_refresh and user_id in self.balance_cache:
        #     cache_entry = self.balance_cache[user_id]
        #     if (current_time - cache_entry['timestamp']) < self.cache_duration:
        #         logger_main.debug(f"Используем кэшированный баланс для пользователя {user_id}")
        #         return cache_entry['balance']
        max_retries = 3
        retry_delay = 2  # Задержка в секундах между попытками
        for attempt in range(max_retries):
            try:
                logger_main.debug(f"Получение баланса (асинхронно) для пользователя {user_id}, попытка {attempt + 1}/{max_retries}")
                # Устанавливаем тайм-аут на уровне HTTP-запроса
                exchange.timeout = 15000  # 15 секунд в миллисекундах
                # Вызываем fetch_balance в асинхронном режиме
                balance = await exchange.fetch_balance()
                # Логируем полный ответ от биржи
                logger_main.debug(f"Полный ответ от биржи для пользователя {user_id}: {balance}")
                # Логируем только USDT баланс для удобства
                usdt_balance = balance.get('USDT', {})
                logger_main.debug(f"USDT баланс для {user_id}: свободно={usdt_balance.get('free', 0)}, заблокировано={usdt_balance.get('used', 0)}, итого={usdt_balance.get('total', 0)}")
                logger_main.debug(f"Баланс успешно получен для пользователя {user_id}: {balance}")
                # Сохраняем баланс в кэш для конкретного пользователя
                self.balance_cache[user_id] = {
                    'balance': balance,
                    'timestamp': current_time
                }
                return balance
            except Exception as e:
                logger_main.error(f"Ошибка при получении баланса для пользователя {user_id} (попытка {attempt + 1}/{max_retries}): {str(e)}")
                log_exception(f"Ошибка при получении баланса: {str(e)}", e)
                if attempt < max_retries - 1:
                    logger_main.debug(f"Повторная попытка через {retry_delay} секунд")
                    await asyncio.sleep(retry_delay)
                else:
                    logger_main.error(f"Все попытки исчерпаны для пользователя {user_id}, приостанавливаем торговлю на {self.suspension_duration} секунд")
                    self.suspended_users[user_id] = current_time + self.suspension_duration
                    return None
        return None

__all__ = ['BalanceManager']
