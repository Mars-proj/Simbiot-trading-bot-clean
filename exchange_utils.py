import asyncio
from utils import logger_main, log_exception

# Список пользователей с недействительными API-ключами
invalid_api_users = set()

# Кэш для недоступных символов (по биржам)
unavailable_symbols = {}

# Кэш для отфильтрованных символов (по биржам)
filtered_symbols_cache = {}

# Кэш для результатов проверки символов (по биржам и символам)
symbol_check_cache = {}

# Ограничение на количество одновременных запросов к API
MAX_CONCURRENT_REQUESTS = 5  # Ограничиваем до 5 параллельных запросов
REQUEST_DELAY = 0.5  # Задержка 0.5 секунды между запросами

# Создаём семафор для ограничения параллельных запросов
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

__all__ = ['invalid_api_users', 'unavailable_symbols', 'filtered_symbols_cache', 'symbol_check_cache', 'semaphore', 'MAX_CONCURRENT_REQUESTS', 'REQUEST_DELAY']
