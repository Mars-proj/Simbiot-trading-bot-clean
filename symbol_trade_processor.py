import asyncio
from logging_setup import logger_main
from utils import log_exception
from market_rentgen_core import market_rentgen
from global_objects import global_trade_pool
from trade_executor_signals import execute_trade

semaphore = asyncio.Semaphore(10)  # Ограничение на 10 параллельных задач

async def process_symbol(exchange, symbol, df, user_id, trade_executor):
    """Обрабатывает отдельный символ для торговли"""
    async with semaphore:
        try:
            analysis = await market_rentgen.get_strategy_recommendation(symbol, df, await global_trade_pool.get_trades_by_symbol(symbol))
            # Выполняем торговлю
            await execute_trade(trade_executor, exchange, symbol, analysis['strategy_name'], user_id, analysis.get('strategy_params'), analysis.get('market_conditions'), analysis.get('success_prob'))
        except Exception as e:
            raise Exception(f"Ошибка при обработке {symbol}: {str(e)}")

__all__ = ['process_symbol']
