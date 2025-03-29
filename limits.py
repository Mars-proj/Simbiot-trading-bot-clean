from utils import logger_main, logger_debug, log_exception
import asyncio
import time
from trade_pool import analyze_trade_pool

class LimitsManager:
    def __init__(self):
        self.limits = {}
        self.lock = asyncio.Lock()

    async def initialize_user(self, user_id, deposit, daily_limit_ratio=0.9):
        async with self.lock:
            if user_id not in self.limits:
                if deposit <= 0:
                    logger_main.warning(f"Недопустимый депозит ({deposit}) для {user_id}, устанавливаем 0")
                    deposit = 0
                self.limits[user_id] = {
                    'deposit': deposit,
                    'daily_limit': deposit * daily_limit_ratio,
                    'daily_used': 0.0,
                    'last_reset': time.time(),
                    'trade_volume': 0.0  # Общий объём торгов за день
                }
            logger_main.info(f"Лимиты для {user_id} инициализированы: {self.limits[user_id]}")

    async def reset_daily_limits(self):
        async with self.lock:
            current_time = time.time()
            for user_id in self.limits:
                if current_time - self.limits[user_id]['last_reset'] >= 86400:  # Сброс каждые 24 часа
                    stats = await analyze_trade_pool(user_id)
                    success_rate = stats['success_rate']
                    if success_rate > 0.7:
                        self.limits[user_id]['daily_limit'] *= 1.1  # Увеличиваем на 10%
                        logger_main.info(f"Увеличен daily_limit для {user_id} на 10% из-за success_rate={success_rate}")
                    elif success_rate < 0.3:
                        self.limits[user_id]['daily_limit'] *= 0.9  # Уменьшаем на 10%
                        logger_main.info(f"Уменьшен daily_limit для {user_id} на 10% из-за success_rate={success_rate}")
                    self.limits[user_id]['daily_used'] = 0.0
                    self.limits[user_id]['trade_volume'] = 0.0
                    self.limits[user_id]['last_reset'] = current_time
                    logger_main.info(f"Сброшены дневные лимиты для {user_id} (по времени)")
                elif self.limits[user_id]['trade_volume'] >= self.limits[user_id]['daily_limit'] * 0.5:  # Сброс при 50% объёма
                    stats = await analyze_trade_pool(user_id)
                    success_rate = stats['success_rate']
                    if success_rate > 0.7:
                        self.limits[user_id]['daily_limit'] *= 1.1
                        logger_main.info(f"Увеличен daily_limit для {user_id} на 10% из-за success_rate={success_rate} (по объёму)")
                    elif success_rate < 0.3:
                        self.limits[user_id]['daily_limit'] *= 0.9
                        logger_main.info(f"Уменьшен daily_limit для {user_id} на 10% из-за success_rate={success_rate} (по объёму)")
                    self.limits[user_id]['daily_used'] = 0.0
                    self.limits[user_id]['trade_volume'] = 0.0
                    self.limits[user_id]['last_reset'] = current_time
                    logger_main.info(f"Сброшены дневные лимиты для {user_id} (по объёму)")

    async def get_trade_amount(self, user_id, current_price):
        async with self.lock:
            if user_id not in self.limits:
                logger_main.warning(f"Лимиты для {user_id} не инициализированы")
                return None
            deposit = self.limits[user_id]['deposit']
            daily_limit = self.limits[user_id]['daily_limit']
            daily_used = self.limits[user_id]['daily_used']
            remaining = daily_limit - daily_used
            logger_main.debug(f"Проверка лимита для {user_id}: deposit={deposit}, daily_limit={daily_limit}, daily_used={daily_used}, remaining={remaining}")
            if remaining <= 0:
                logger_main.warning(f"Дневной лимит для {user_id} исчерпан: remaining={remaining}")
                return None
            fee_rate = 0.003  # Комиссия 0.3%
            min_trade_usdt = 10.0 / (1 - fee_rate)  # ≈ 10.03 USDT
            trade_amount_usdt = max(min(remaining, deposit * 0.01), min_trade_usdt)  # Не более 1% депозита
            logger_main.debug(f"trade_amount_usdt для {user_id}: {trade_amount_usdt}, min_trade_usdt={min_trade_usdt}")
            if trade_amount_usdt < min_trade_usdt:
                logger_main.warning(f"Сумма сделки ({trade_amount_usdt} USDT) меньше минимальной ({min_trade_usdt} USDT) для {user_id}")
                return None
            trade_amount = trade_amount_usdt / current_price
            self.limits[user_id]['daily_used'] += trade_amount_usdt
            self.limits[user_id]['trade_volume'] += trade_amount_usdt  # Учитываем объём торгов
            logger_main.debug(f"После расчёта trade_amount для {user_id}: trade_amount={trade_amount}, daily_used={self.limits[user_id]['daily_used']}, trade_volume={self.limits[user_id]['trade_volume']}")
            return trade_amount

    async def update_trade_volume(self, user_id, trade_amount_usdt):
        async with self.lock:
            if user_id in self.limits:
                self.limits[user_id]['trade_volume'] += trade_amount_usdt
                logger_main.debug(f"Обновлён trade_volume для {user_id}: {self.limits[user_id]['trade_volume']}")

limits_manager = LimitsManager()
