import asyncio
import json
import os
import time
from logging_setup import logger_main
from exchange_pool import ExchangePool
from market_state_analyzer import analyze_market_state, calculate_dynamic_thresholds
from symbol_filter import filter_symbols
from trading_manager import run_trading_for_user

async def process_user(user, exchange_id, exchange_pool, symbols, backtest_results, dynamic_thresholds, market_state, semaphore):
    """Processes a single user with rate limiting."""
    async with semaphore:
        logger_main.info(f"Processing user {user['user_id']}")
        try:
            valid_symbols = await run_trading_for_user(
                user, exchange_id, None, 90, exchange_pool, symbols, backtest_results, dynamic_thresholds, market_state
            )
            logger_main.info(f"Completed processing for user {user['user_id']} with {len(valid_symbols)} valid symbols")
        except Exception as e:
            logger_main.error(f"Error processing user {user['user_id']}: {e}")

async def main():
    logger_main.info("Starting process_users")
    
    # Load selected pairs
    logger_main.info("Checking for selected pairs file: selected_pairs.json")
    if not os.path.exists("selected_pairs.json"):
        logger_main.error("Selected pairs file not found")
        return
    logger_main.info("Selected pairs file exists, loading symbols")
    with open("selected_pairs.json", "r") as f:
        symbols = json.load(f)
    logger_main.info(f"Loaded {len(symbols)} selected pairs from selected_pairs.json: {symbols[:5]}...")

    # Load backtest results
    logger_main.info("Checking for backtest results file: backtest_results.json")
    if not os.path.exists("backtest_results.json"):
        logger_main.error("Backtest results file not found")
        return
    logger_main.info("Backtest results file exists, loading results")
    with open("backtest_results.json", "r") as f:
        backtest_results = json.load(f)
    logger_main.info(f"Loaded backtest results for {len(backtest_results)} symbols from backtest_results.json")

    # Initialize exchange pool
    exchange_pool = ExchangePool()

    # Analyze market state
    logger_main.info("Analyzing market state")
    market_state = await analyze_market_state(exchange_pool, "mexc")
    logger_main.info(f"Market state determined: {market_state}")
    
    if market_state == "unknown":
        logger_main.error("Failed to determine market state, aborting")
        return

    # Calculate dynamic thresholds
    logger_main.info("Calculating dynamic thresholds")
    dynamic_thresholds = await calculate_dynamic_thresholds(exchange_pool, "mexc", backtest_results, market_state)

    # Process users in parallel with rate limiting
    users = [
        {"user_id": "user1", "testnet": False},
        {"user_id": "user2", "testnet": False},
        {"user_id": "user3", "testnet": False},
    ]

    # Simulate 1000+ users for scalability testing
    # Uncomment the following block to test with 1000 users
    # users = [{"user_id": f"user{i}", "testnet": False} for i in range(1, 1001)]

    # Semaphore to limit concurrent user processing (e.g., 50 users at a time)
    semaphore = asyncio.Semaphore(50)  # Adjust based on system resources and API limits

    tasks = []
    for user in users:
        task = asyncio.create_task(process_user(
            user, "mexc", exchange_pool, symbols, backtest_results, dynamic_thresholds, market_state, semaphore
        ))
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)

    # Close exchange pool
    await exchange_pool.close_all()

if __name__ == "__main__":
    asyncio.run(main())
