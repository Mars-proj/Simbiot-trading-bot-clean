# backtester.py
import logging

logger = logging.getLogger("main")

async def backtest_strategy(historical_data, signals):
    """Бэктестит стратегию на исторических данных."""
    profit = 0
    position = None
    for i in range(len(historical_data)):
        signal = signals[i]
        price = historical_data[i]['close']

        if signal == "buy" and position is None:
            position = price  # Открываем позицию (покупка)
        elif signal == "sell" and position is not None:
            profit += (price - position)  # Закрываем позицию (продажа)
            position = None

    return profit
