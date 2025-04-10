import asyncio
import logging
import os
from user_manager import UserManager
from start_trading_all import start_trading_all
from exchange_pool import ExchangePool

# Настройка логирования
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting main execution")
    
    # Инициализация менеджера пользователей
    user_manager = UserManager()
    await user_manager.connect()  # Инициализация подключения к базе данных
    
    # Инициализация пула бирж
    exchange_pool = ExchangePool()
    
    # Пример данных
    users = ['main_user']
    credentials = {
        'main_user': {
            'api_key': 'mx0vglM30RTqlJzTGF',
            'api_secret': '74320c83880348768a6b68973d50854b'
        }
    }
    since = 1609459200000  # Пример: 1 января 2021 года в миллисекундах
    limit = 1000
    timeframe = '1h'
    symbol_batch = ['BTC/USDT', 'ETH/USDT']
    
    # SMTP credentials для Proton Mail
    smtp_user = "simbiotai@proton.me"
    smtp_password = "osoznanie_soznaniya"
    
    try:
        # Запуск торгов для всех пользователей
        await start_trading_all(
            users, credentials, since, limit, timeframe, symbol_batch, exchange_pool, smtp_user, smtp_password
        )
    finally:
        # Закрытие подключений
        await user_manager.close()
        await exchange_pool.close()

if __name__ == "__main__":
    asyncio.run(main())
