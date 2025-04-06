from logging_setup import logger_main

async def start_trading_all(user, exchange_id, symbols, exchange):
    """Starts trading for a user on the specified exchange with the given symbols."""
    logger_main.info(f"Starting trading for user {user['user_id']} on {exchange_id} with {len(symbols)} symbols")
    logger_main.debug(f"Exchange instance: {exchange}")
    
    if exchange is None:
        logger_main.error("Exchange instance is None, cannot execute trades")
        return

    for symbol in symbols:
        try:
            logger_main.info(f"Trading {symbol} for user {user['user_id']} on {exchange_id}")
            # Place a market buy order for the symbol
            amount = 0.1  # Example amount, adjust based on your strategy
            logger_main.debug(f"Placing market buy order for {symbol} with amount {amount}")
            order = await exchange.create_market_buy_order(symbol, amount)
            logger_main.info(f"Trade executed for {symbol} on {exchange_id}: {order}")
        except Exception as e:
            logger_main.error(f"Failed to execute trade for {symbol} on {exchange_id}: {e}")

async def run_backtest(exchange_id, user_id, symbols, backtest_days, testnet=False):
    """Runs a backtest for the given symbols."""
    logger_main.info(f"Running backtest for user {user_id} on {exchange_id} with {len(symbols)} symbols for {backtest_days} days")
    backtest_results = {}
    for symbol in symbols:
        backtest_results[symbol] = {'profit': 0.05}  # Example profit value
    return backtest_results
