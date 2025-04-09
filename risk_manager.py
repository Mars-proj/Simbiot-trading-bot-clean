from features import calculate_volatility

async def set_stop_loss(exchange, symbol, amount, entry_price, volatility):
    """
    Set a stop-loss for a position with dynamic adjustment based on volatility.

    Args:
        exchange: Exchange instance.
        symbol (str): Trading symbol.
        amount (float): Amount to trade.
        entry_price (float): Entry price.
        volatility (float): Market volatility.

    Returns:
        dict: Sell order if triggered, None otherwise.
    """
    stop_loss_percent = 0.02 + volatility * 0.005  # Динамический стоп-лосс
    ticker = await exchange.fetch_ticker(symbol)
    current_price = ticker['last']
    stop_price = entry_price * (1 - stop_loss_percent)
    if current_price <= stop_price:
        return await exchange.create_market_sell_order(symbol, amount)
    return None

async def set_trailing_stop(exchange, symbol, amount, entry_price, trailing_percent=0.01):
    """
    Set a trailing stop for a position.

    Args:
        exchange: Exchange instance.
        symbol (str): Trading symbol.
        amount (float): Amount to trade.
        entry_price (float): Entry price.
        trailing_percent (float): Trailing stop percentage (default: 0.01).

    Returns:
        dict: Sell order if triggered, None otherwise.
    """
    ticker = await exchange.fetch_ticker(symbol)
    current_price = ticker['last']
    highest_price = max(entry_price, current_price)  # Отслеживаем максимальную цену
    stop_price = highest_price * (1 - trailing_percent)
    if current_price <= stop_price:
        return await exchange.create_market_sell_order(symbol, amount)
    return None

async def calculate_exit_points(position, current_price, profit_target=0.05, stop_loss=0.02):
    """
    Calculate exit points for a position.

    Args:
        position (dict): Position details.
        current_price (float): Current price.
        profit_target (float): Profit target percentage (default: 0.05).
        stop_loss (float): Stop-loss percentage (default: 0.02).

    Returns:
        dict: Exit points (take-profit and stop-loss).
    """
    entry_price = position['price']
    take_profit = entry_price * (1 + profit_target)
    stop_loss_price = entry_price * (1 - stop_loss)
    return {"take_profit": take_profit, "stop_loss": stop_loss_price}
