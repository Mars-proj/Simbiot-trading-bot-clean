import asyncio
from logging_setup import logger_main
from start_trading_all import start_trading_all
from symbol_filter import filter_symbols

async def run_trading_for_user(user, exchange_id, model_path, backtest_days, exchange_pool, symbols, backtest_results, dynamic_thresholds, market_state):
    """Runs trading for a single user with the given parameters."""
    logger_main.info(f"Entering run_trading_for_user for user {user['user_id']} on {exchange_id}")
    
    # Fetch the exchange instance
    logger_main.info(f"Starting trading for user {user['user_id']} on {exchange_id}")
    exchange = await exchange_pool.get_exchange(exchange_id, user['user_id'], testnet=user['testnet'])
    if not exchange:
        logger_main.error(f"Failed to get exchange instance for {exchange_id}:{user['user_id']}")
        return
    
    logger_main.debug(f"Exchange instance created: {exchange}")
    
    # Filter symbols for trading
    logger_main.info(f"Calling filter_symbols for user {user['user_id']}")
    valid_symbols = await filter_symbols(
        symbols,
        backtest_results,
        user['user_id'],
        exchange_pool,
        exchange_id,
        dynamic_thresholds,
        market_state
    )
    
    logger_main.info(f"filter_symbols returned {len(valid_symbols)} valid symbols for user {user['user_id']}")
    if not valid_symbols:
        logger_main.warning(f"No valid symbols for trading for user {user['user_id']}, skipping")
        return
    
    logger_main.info(f"Starting trading with {len(valid_symbols)} symbols for user {user['user_id']}: {valid_symbols[:5]}...")
    
    # Start trading tasks
    trade_task = asyncio.create_task(start_trading_all(user, exchange_id, valid_symbols, exchange))
    logger_main.debug(f"Creating trade_task for user {user['user_id']}")
    
    # Placeholder for other tasks (cleanup, monitoring, retraining)
    cleanup_task = asyncio.create_task(asyncio.sleep(1))  # Placeholder
    logger_main.debug(f"Creating cleanup_task for user {user['user_id']}")
    
    monitor_task = asyncio.create_task(asyncio.sleep(1))  # Placeholder
    logger_main.debug(f"Creating monitor_task for user {user['user_id']}")
    
    retrain_task = asyncio.create_task(asyncio.sleep(1))  # Placeholder
    logger_main.debug(f"Creating retrain_task for user {user['user_id']}")
    
    # Run tasks
    logger_main.info(f"Starting tasks for user {user['user_id']}: trade, cleanup, monitor")
    await asyncio.gather(trade_task, cleanup_task, monitor_task, retrain_task)
    
    return valid_symbols
