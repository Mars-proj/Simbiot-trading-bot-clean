from logging_setup import logger_main
from bot_user_data import BotUserData

async def collect_training_data(exchange_id, user_id):
    """Collects training data from trade pool and user cache."""
    try:
        bot_user_data = BotUserData()
        trades = await bot_user_data.get_user_trades(user_id)
        if not trades:
            logger_main.warning(f"No trades found for user {user_id} on {exchange_id}")
            return None

        # Преобразовать сделки в тренировочные данные
        training_data = []
        for trade in trades:
            features = {
                'symbol': trade['symbol'],
                'price': trade['price'],
                'volume': trade['volume'],
                'profit_loss': trade['profit_loss'],
                # Добавить рыночные данные (OHLCV, индикаторы) в будущем
            }
            training_data.append(features)
        logger_main.info(f"Collected {len(training_data)} training data points for user {user_id} on {exchange_id}")
        return training_data
    except Exception as e:
        logger_main.error(f"Error collecting training data for user {user_id} on {exchange_id}: {e}")
        return None

__all__ = ['collect_training_data']
