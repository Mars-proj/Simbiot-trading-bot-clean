import asyncio
import ccxt.async_support as ccxt
from logging_setup import shutdown_loggers
from symbol_handler import process_symbols
from trade_executor_core import TradeExecutor
from trade_executor_signals import generate_signal, execute_trade
from risk_manager import risk_manager
from market_rentgen_core import market_rentgen
from ml_predictor import ml_predictor
from global_objects import global_trade_pool

async def process_user(user, exchange, trade_executor, can_trade_dict, preferred_exchange, semaphore, logger_main):
    """Processes a single user in the trading cycle with semaphore for limiting concurrency"""
    async with semaphore:
        if not can_trade_dict[user]:
            logger_main.info(f"Skipping user {user} due to exceeding drawdown")
            return
        logger_main.info(f"Processing user {user}")
        # Symbols will be chosen dynamically in process_symbols based on available tokens
        await process_symbols(exchange, user, preferred_exchange, trade_executor, symbols=None)

async def main():
    # Import logger_main here to ensure it's initialized
    from logging_setup import logger_main
    # Import API_KEYS and PREFERRED_EXCHANGES here to avoid import issues
    from config import API_KEYS, PREFERRED_EXCHANGES
    logger_main.info("Starting trading cycle")
    # Initialize logging for global objects
    risk_manager.initialize_logging()
    # Create a dictionary to store exchanges
    exchanges = {}
    # Set up users
    users = list(API_KEYS.keys())
    logger_main.info(f"Found {len(users)} users to set up")
    # Set up exchanges for each user
    for user in users:
        logger_main.info(f"Setting up user {user}")
        preferred_exchange = PREFERRED_EXCHANGES[user]
        exchange_config = API_KEYS[user][preferred_exchange]
        exchange_class = getattr(ccxt, preferred_exchange)
        exchange = exchange_class(exchange_config)
        exchanges[user] = exchange
        logger_main.info(f"Exchange {preferred_exchange} set up for user {user}")
    # Initialize MarketRentgen for each exchange to avoid caching a single exchange
    for user, exchange in exchanges.items():
        logger_main.info(f"Initializing MarketRentgen for {user}")
        await market_rentgen.initialize(exchange)
    # Initialize TradeExecutor
    trade_executor = TradeExecutor(risk_manager)
    trade_executor.initialize_logging()
    # Initialize deposit for each user and check balance
    user_deposits = {}  # Dictionary to store user deposits
    active_users = []  # List of users with non-zero deposits
    for user in users:
        logger_main.info(f"Initializing deposit for user {user}")
        await trade_executor.initialize_deposit(exchanges[user], user)
        total_deposit = await trade_executor.deposit_manager.calculate_total_deposit(exchanges[user], user)
        user_deposits[user] = total_deposit
        if total_deposit > 0:
            active_users.append(user)
            logger_main.info(f"User {user} added to active users with deposit {total_deposit} USDT")
        else:
            logger_main.warning(f"User {user} excluded from active users: deposit is 0")
    if not active_users:
        logger_main.error("No active users with non-zero deposit, shutting down")
        return
    # Start trading cycle
    last_retrain_time = asyncio.get_event_loop().time()
    can_trade_dict = {user: True for user in active_users}  # Dictionary to store can_trade status
    error_count = 0  # Counter for consecutive errors
    max_consecutive_errors = 5  # Maximum allowed consecutive errors before increasing wait time
    max_users_concurrent = 10  # Maximum number of users to process concurrently
    semaphore = asyncio.Semaphore(max_users_concurrent)  # Limit concurrent user processing
    while True:
        logger_main.info(f"Starting new trading cycle with {len(active_users)} active users")
        cycle_start_time = asyncio.get_event_loop().time()
        try:
            # Check drawdown for each user
            logger_main.info("Checking drawdown before cycle")
            can_trade = True
            for user in active_users:
                can_trade_dict[user] = await trade_executor.risk_calculator.check_drawdown(exchanges[user], user, trade_executor.deposit_manager)
                if not can_trade_dict[user]:
                    logger_main.warning(f"Trading paused for {user} due to exceeding max drawdown")
                    can_trade = False
            if not can_trade:
                logger_main.warning("Trading paused for all users due to exceeding max drawdown")
                await asyncio.sleep(60)  # Wait 1 minute before next check
                continue
            # Process users in parallel with semaphore
            tasks = []
            for user in active_users:
                task = process_user(user, exchanges[user], trade_executor, can_trade_dict, PREFERRED_EXCHANGES[user], semaphore, logger_main)
                tasks.append(task)
            await asyncio.gather(*tasks, return_exceptions=True)
            # Check if ML models need retraining
            current_time = asyncio.get_event_loop().time()
            # Dynamic retrain interval based on number of trades and model accuracy
            recent_trades = await global_trade_pool.get_recent_trades(limit=100)
            trade_frequency = len(recent_trades) / 100  # Normalize to a factor
            retrain_interval = 3600 * (1 + trade_frequency)  # Increase interval with more trades
            # Check model accuracy (if available)
            model_accuracy = await ml_predictor.get_model_accuracy() if hasattr(ml_predictor, 'get_model_accuracy') else 1.0
            if model_accuracy < 0.6:  # If accuracy drops below 60%, retrain immediately
                logger_main.info(f"Model accuracy low ({model_accuracy:.2%}), forcing retraining")
                await ml_predictor.retrain()
                last_retrain_time = current_time
            elif current_time - last_retrain_time >= retrain_interval:
                logger_main.info(f"Retraining ML model: elapsed time: {(current_time - last_retrain_time)/3600:.2f} hours")
                await ml_predictor.retrain()
                last_retrain_time = current_time
            # Save backtest trades to trade_pool
            logger_main.info("Fetching backtest trades to save in trade_pool")
            trades = await global_trade_pool.get_all_trades(source='backtest')
            if trades:
                logger_main.info(f"Saving {len(trades)} backtest trades to trade_pool")
                for trade in trades:
                    trade['source'] = 'backtest'
                    await global_trade_pool.add_trade(trade)
            else:
                logger_main.info("No backtest trades found")
            # Dynamic sleep interval based on market conditions and number of users
            market_conditions = await market_rentgen.get_market_conditions() if hasattr(market_rentgen, 'get_market_conditions') else {}
            avg_volatility = market_conditions.get('avg_volatility', 0.0)
            sleep_interval = 60 * (1 + len(active_users) / 10)  # Base interval
            if avg_volatility > 0.1:  # High volatility
                sleep_interval *= 0.5  # Reduce interval for faster cycles
            elif avg_volatility < 0.05:  # Low volatility
                sleep_interval *= 1.5  # Increase interval for stability
            cycle_duration = asyncio.get_event_loop().time() - cycle_start_time
            logger_main.info(f"Cycle completed in {cycle_duration:.2f} seconds, waiting {sleep_interval:.2f} seconds before the next cycle")
            error_count = 0  # Reset error count on successful cycle
            await asyncio.sleep(sleep_interval)
        except Exception as e:
            logger_main.error(f"Error in trading cycle: {str(e)}")
            error_count += 1
            wait_time = 60 * (1 + error_count)  # Increase wait time with more consecutive errors
            if error_count >= max_consecutive_errors:
                logger_main.error(f"Too many consecutive errors ({error_count}), shutting down")
                break
            logger_main.info(f"Waiting {wait_time} seconds before retrying due to {error_count} consecutive errors")
            await asyncio.sleep(wait_time)

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger_main.info("Program stopped by user")
    finally:
        shutdown_loggers()
