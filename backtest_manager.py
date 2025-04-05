import asyncio
from logging_setup import logger_main
from start_trading_all import run_backtest

async def run_backtests(exchange_id, user_id, symbols, backtest_days, testnet):
    """Runs backtests for all symbols in parallel and returns results."""
    backtest_results = {}
    batch_size = 20  # Increased batch size for parallel backtesting
    logger_main.info(f"Starting backtest for {len(symbols)} symbols in batches of {batch_size}")
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        logger_main.info(f"Processing backtest batch {i//batch_size + 1} of {len(symbols)//batch_size + 1} (symbols {i} to {min(i + batch_size, len(symbols))})")
        tasks = []
        for symbol in batch:
            tasks.append(asyncio.create_task(run_backtest(
                exchange_id, user_id, symbol,
                days=backtest_days,
                leverage=1.0,
                trade_percentage=0.1,
                rsi_overbought=70,
                rsi_oversold=30,
                test_mode=testnet
            )))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for symbol, result in zip(batch, results):
            if isinstance(result, Exception):
                logger_main.warning(f"Backtest failed for {symbol}: {result}")
                backtest_results[symbol] = None
            else:
                backtest_results[symbol] = result
                logger_main.debug(f"Backtest result for {symbol}: {result}")
    logger_main.info(f"Backtest completed for {len(backtest_results)} symbols")
    return backtest_results
