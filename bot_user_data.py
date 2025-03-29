from logging_setup import logger_main

# Данные пользователей (реальные данные для работы)
user_data = {
    "8d99788d-f58f-4fb8-9e4d-c05f177f5405": {
        "total_deposit_usdt": 100.0,
        "assets": {
            "USDT": {"free": 100.0, "locked": 0.0, "total": 100.0}
        },
        "trades": []
    }
}

def get_user_deposit(user_id):
    """Возвращает депозит пользователя"""
    deposit = user_data.get(user_id, {}).get("total_deposit_usdt", 0.0)
    logger_main.debug(f"User {user_id} deposit: {deposit} USDT")
    return deposit

def get_user_assets(user_id):
    """Возвращает активы пользователя"""
    assets = user_data.get(user_id, {}).get("assets", {})
    logger_main.debug(f"User {user_id} assets: {assets}")
    return assets

def add_user_trade(user_id, trade_log, signal, strategy_signals):
    """Добавляет сделку для пользователя"""
    if user_id in user_data:
        user_data[user_id]["trades"].append({
            "trade": trade_log,
            "signal": signal,
            "strategy_signals": strategy_signals
        })
        logger_main.debug(f"Added trade for user {user_id}: {trade_log}")
    else:
        logger_main.warning(f"User {user_id} not found in user_data, cannot add trade")

def update_user_data(user_id, data):
    """Обновляет данные пользователя"""
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id].update(data)
    logger_main.debug(f"Updated user data for {user_id}: {data}")

__all__ = ['user_data', 'get_user_deposit', 'get_user_assets', 'add_user_trade', 'update_user_data']
