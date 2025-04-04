# trade_executor_core.py
from logging_setup import logger_main
from trade_pool_core import TradePoolCore  # Заменили TradePool на TradePoolCore

async def execute_buy_trade(user_id, exchange_id, symbol, amount):
    trade_pool = TradePoolCore(user_id, exchange_id)  # Заменили TradePool на TradePoolCore
    logger_main.info(f"Executing buy trade for {symbol} on {exchange_id} for user {user_id}")
    # Здесь логика выполнения покупки
    trade = {"type": "buy", "symbol": symbol, "amount": amount}  # Заглушка
    return trade

async def execute_sell_trade(user_id, exchange_id, symbol, amount):
    trade_pool = TradePoolCore(user_id, exchange_id)  # Заменили TradePool на TradePoolCore
    logger_main.info(f"Executing sell trade for {symbol} on {exchange_id} for user {user_id}")
    # Здесь логика выполнения продажи
    trade = {"type": "sell", "symbol": symbol, "amount": amount}  # Заглушка
    return trade
