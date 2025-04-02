from logging_setup import logger_main
from bot_trading import run_trading_bot
from market_analyzer import analyze_market_conditions
import asyncio

async def start_trading_all(exchange_id, user_id, symbols, leverage, order_type, trade_percentage, rsi_overbought, rsi_oversold, margin_multiplier, blacklisted_symbols, model_path, test_mode):
    """Starts trading for all symbols."""
    try:
        logger_main.info(f"Starting trading for user {user_id} on {exchange_id} with symbols: {symbols[:5]}...")

        # Analyze market conditions to adapt parameters
        market_conditions = await analyze_market_conditions(exchange_id, user_id, testnet=test_mode)
        if market_conditions:
            market_volatility = market_conditions['market_volatility']
            leverage = min(5.0, 1.0 + market_volatility * 0.1)  # Увеличиваем кредитное плечо при высокой волатильности
            trade_percentage = max(0.05, 0.1 - market_volatility * 0.01)  # Уменьшаем процент при высокой волатильности
            logger_main.info(f"Adapted parameters: leverage={leverage}, trade_percentage={trade_percentage}")

        # Start trading for each symbol
        tasks = []
        for symbol in symbols:
            if symbol in blacklisted_symbols:
                logger_main.warning(f"Symbol {symbol} is blacklisted, skipping")
                continue
            task = asyncio.create_task(run_trading_bot(
                exchange_id, user_id, symbol,
                leverage=leverage,
                order_type=order_type,
                trade_percentage=trade_percentage,
                rsi_overbought=rsi_overbought,
                rsi_oversold=rsi_oversold,
                margin_multiplier=margin_multiplier,
                model_path=model_path,
                test_mode=test_mode
            ))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                logger_main.error(f"Trading failed for {symbol} on {exchange_id}: {result}")
            else:
                logger_main.info(f"Trading result for {symbol} on {exchange_id}: {result}")
    except Exception as e:
        logger_main.error(f"Error in start_trading_all for user {user_id} on {exchange_id}: {e}")

__all__ = ['start_trading_all']
