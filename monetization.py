from logging_setup import logger_main

class Monetization:
    def __init__(self):
        # Уровни пользователей и комиссии
        self.levels = {
            "Новичок": {"deposit_range": (0, 1000), "commission": 0.30},
            "Профессионал": {"deposit_range": (1000, 5000), "commission": 0.25},
            "VIP": {"deposit_range": (5000, float("inf")), "commission": 0.20}
        }

    def get_user_level(self, deposit):
        """Определяет уровень пользователя на основе депозита."""
        for level, info in self.levels.items():
            min_deposit, max_deposit = info["deposit_range"]
            if min_deposit <= deposit < max_deposit:
                return level
        return "Новичок"  # По умолчанию

    def calculate_commission(self, deposit, profit):
        """Рассчитывает комиссию на основе депозита и прибыли."""
        level = self.get_user_level(deposit)
        commission_rate = self.levels[level]["commission"]
        commission = profit * commission_rate
        logger_main.info(f"User level: {level}, Deposit: ${deposit}, Profit: ${profit}, Commission rate: {commission_rate*100}%, Commission: ${commission}")
        return commission

monetization = Monetization()

__all__ = ['monetization']
