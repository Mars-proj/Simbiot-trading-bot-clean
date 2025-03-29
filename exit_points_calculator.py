from utils import logger_main

def calculate_dynamic_exit_points(market_conditions, symbol, entry_price, base_stop_loss_percentage=0.02, base_take_profit_drop=0.02):
    """
    Вычисляет динамические Stop-Loss и Take-Profit на основе рыночных условий.
    Аргументы:
    - market_conditions: Словарь с рыночными условиями (avg_volatility).
    - symbol: Символ (например, 'BTC/USDT').
    - entry_price: Цена входа.
    - base_stop_loss_percentage: Базовый процент Stop-Loss (по умолчанию 0.02 = 2%).
    - base_take_profit_drop: Базовый процент падения для Take-Profit (по умолчанию 0.02 = 2%).
    Возвращает:
    - stop_loss_price: Цена Stop-Loss.
    - take_profit_drop: Процент падения для Take-Profit.
    """
    logger_main.debug(f"Вычисление динамических точек выхода для {symbol}")
    try:
        # Получаем волатильность рынка
        volatility = market_conditions.get('avg_volatility', 0.0)
        # Динамический Stop-Loss: увеличиваем при высокой волатильности
        stop_loss_percentage = base_stop_loss_percentage * (1 + volatility * 10)
        stop_loss_percentage = min(stop_loss_percentage, 0.1)  # Ограничиваем максимум 10%
        # Динамический Take-Profit: увеличиваем при высокой волатильности
        take_profit_drop = base_take_profit_drop * (1 + volatility * 5)
        take_profit_drop = min(take_profit_drop, 0.05)  # Ограничиваем максимум 5%
        stop_loss_price = entry_price * (1 - stop_loss_percentage)
        logger_main.debug(f"Динамический Stop-Loss для {symbol}: {stop_loss_price:.4f} (процент: {stop_loss_percentage:.2%})")
        logger_main.debug(f"Динамический Take-Profit для {symbol}: падение от пика {take_profit_drop:.2%}")
        return stop_loss_price, take_profit_drop
    except Exception as e:
        logger_main.error(f"Ошибка при вычислении динамических точек выхода для {symbol}: {str(e)}")
        return entry_price * (1 - base_stop_loss_percentage), base_take_profit_drop

__all__ = ['calculate_dynamic_exit_points']
