# symbol_trade_processor.py
from logging_setup import logger_main
from trade_pool_core import TradePoolCore  # Заменили TradePool на TradePoolCore

async def process_symbol_trades(user_id, exchange_id, symbol):
    trade_pool = TradePoolCore(user_id, exchange_id)  # Заменили TradePool на TradePoolCore
    trades = await trade_pool.fetch_trades(exchange_id, user_id)
    logger_main.info(f"Processing trades for {symbol} on {exchange_id} for user {user_id}: {len(trades)} trades found")
    # Здесь логика обработки сделок для символа
    return trades
