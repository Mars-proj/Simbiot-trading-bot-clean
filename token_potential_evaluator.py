from utils import logger_main

class TokenPotentialEvaluator:
    async def evaluate_token_potential(self, exchange, symbol, signal_metrics, combined_signal):
        """Оценка потенциального профита токена на основе торговой логики"""
        # Используем combined_signal как индикатор силы сигнала
        signal_strength = abs(combined_signal) if combined_signal is not None else 0
        # Учитываем волатильность (ATR) и тренд (short_ma/long_ma)
        atr = signal_metrics.get('atr', 0) if signal_metrics else 0
        trend_factor = 1.0
        if signal_metrics and 'short_ma' in signal_metrics and 'long_ma' in signal_metrics:
            short_ma = signal_metrics['short_ma']
            long_ma = signal_metrics['long_ma']
            if short_ma > long_ma:
                trend_factor = 1.5  # Восходящий тренд
            elif short_ma < long_ma:
                trend_factor = 0.5  # Нисходящий тренд
        # Потенциальный профит: комбинация силы сигнала, волатильности и тренда
        potential_profit = signal_strength * atr * trend_factor
        return potential_profit

__all__ = ['TokenPotentialEvaluator']
