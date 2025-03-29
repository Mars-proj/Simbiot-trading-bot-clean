import asyncio
import time
from logging_setup import logger_main, logger_exceptions
from redis_client import redis_client
from global_objects import global_trade_pool
from bot_user_data import user_data

# Интервал проверки (24 часа)
TRANSFER_INTERVAL = 24 * 60 * 60  # Можно сделать динамическим через конфигурацию

async def transfer_trades_to_pool():
    """Переносит сделки из кэша пользователей в общий пул раз в 24 часа"""
    while True:
        try:
            logger_main.info("Starting trade transfer to global pool")
            current_time = int(time.time())
            # Получаем всех пользователей из user_data
            users = list(user_data.keys())
            for user_id in users:
                # Получаем сделки из кэша
                trades = await redis_client.get_trades_from_cache(user_id)
                if not trades:
                    continue
                # Фильтруем сделки за последние 24 часа
                recent_trades = [trade for trade in trades if (current_time - trade['timestamp']) <= TRANSFER_INTERVAL]
                for trade_info in recent_trades:
                    trade = trade_info['trade']
                    # Добавляем дополнительные данные для переобучения
                    trade['signal'] = trade_info['signal']
                    trade['strategies'] = trade_info['strategies']
                    await global_trade_pool.add_trade(trade)
                    logger_main.debug(f"Transferred trade to global pool for user {user_id}: {trade}")
                # Обновляем кэш, оставляя только сделки младше 24 часов
                remaining_trades = [trade for trade in trades if trade not in recent_trades]
                if remaining_trades:
                    await redis_client.set_json(f"trades:{user_id}", remaining_trades, expire=72*60*60)
                else:
                    await redis_client._client.delete(f"trades:{user_id}")
            logger_main.info("Trade transfer to global pool completed")
            # Ждём 24 часа до следующей проверки
            await asyncio.sleep(TRANSFER_INTERVAL)
        except Exception as e:
            logger_main.error(f"Error transferring trades to global pool: {str(e)}")
            logger_exceptions.error(f"Error transferring trades: {str(e)}", exc_info=True)
            await asyncio.sleep(TRANSFER_INTERVAL)  # Продолжаем после ошибки

# Запуск задачи переноса
def start_trade_transfer():
    """Запускает задачу переноса сделок в фоновом режиме"""
    asyncio.create_task(transfer_trades_to_pool())

__all__ = ['start_trade_transfer']
