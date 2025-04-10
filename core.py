import asyncio
import logging
from user_manager import UserManager
from start_trading_all import start_trading_all

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
    exchange_pool = None  # Здесь должен быть объект ExchangePool, но для примера оставим None
    
    # Запуск торгов для всех пользователей
    await start_trading_all(users, credentials, since, limit, timeframe, symbol_batch, exchange_pool)
    
    # Закрытие подключения
    await user_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
