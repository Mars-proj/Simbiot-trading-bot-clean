import asyncio
from trade_pool_queries import get_all_trades as get_trade_pool
from logging_setup import logger_main

async def check_trades_for_user(user_id):
    logger_main.info(f"Получение сделок для пользователя {user_id}")
    trades = await get_trade_pool()
    user_trades = [trade for trade in trades if trade.get('user_id') == user_id]
    if not user_trades:
        logger_main.info(f"Сделки для пользователя {user_id} не найдены")
    else:
        logger_main.info(f"Найдено {len(user_trades)} сделок для пользователя {user_id}")
        for trade in user_trades:
            logger_main.info(f"Сделка: {trade}")
    return user_trades

if __name__ == "__main__":
    user_id = "USER1"
    asyncio.run(check_trades_for_user(user_id))
