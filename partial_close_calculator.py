from utils import logger_main

def calculate_partial_close_amount(position_amount, profit_pct, min_profit_threshold=5.0, close_percentage=0.5):
    """
    Рассчитывает количество для частичного закрытия позиции.
    Аргументы:
    - position_amount: Текущий объём позиции.
    - profit_pct: Текущая прибыль в процентах.
    - min_profit_threshold: Минимальный порог прибыли для частичного закрытия (по умолчанию 5%).
    - close_percentage: Процент позиции для частичного закрытия (по умолчанию 0.5 = 50%).
    Возвращает:
    - close_amount: Объём для частичного закрытия (0, если прибыль недостаточна).
    """
    if profit_pct >= min_profit_threshold:
        close_amount = position_amount * close_percentage
        logger_main.info(f"Рассчитано частичное закрытие: {close_amount} из {position_amount} для прибыли {profit_pct:.2f}%")
        return close_amount
    else:
        logger_main.info(f"Прибыль {profit_pct:.2f}% недостаточна для частичного закрытия (требуется минимум {min_profit_threshold}%)")
        return 0.0

__all__ = ['calculate_partial_close_amount']
