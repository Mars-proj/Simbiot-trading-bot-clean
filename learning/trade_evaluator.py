# learning/trade_evaluator.py
import logging
import redis.asyncio as redis
import json
import numpy as np

logger = logging.getLogger("main")

async def get_redis_client():
    """Инициализация Redis клиента."""
    return await redis.from_url("redis://localhost:6379/0")

async def evaluate_trade(symbol, user, strategy, profit):
    """Оценивает успешность сделки и обновляет статистику стратегии в Redis."""
    redis_client = await get_redis_client()
    try:
        # Update symbol-specific trade success
        symbol_key = f"trade_success:{symbol}:{user}"
        symbol_data = await redis_client.get(symbol_key)
        if symbol_data:
            symbol_data = json.loads(symbol_data.decode())
        else:
            symbol_data = {'total_trades': 0, 'successful_trades': 0}

        symbol_data['total_trades'] += 1
        if profit > 0:
            symbol_data['successful_trades'] += 1

        await redis_client.set(symbol_key, json.dumps(symbol_data), ex=86400 * 30)

        # Update strategy-specific success
        strategy_key = f"strategy_success:{strategy['name']}:{symbol}:{user}"
        strategy_data = await redis_client.get(strategy_key)
        if strategy_data:
            strategy_data = json.loads(strategy_data.decode())
        else:
            strategy_data = {
                'name': strategy['name'],
                'indicators': strategy.get('indicators', []),
                'total_trades': 0,
                'successful_trades': 0,
                'total_profit': 0,
                'parameters': strategy.get('parameters', {})
            }

        strategy_data['total_trades'] += 1
        if profit > 0:
            strategy_data['successful_trades'] += 1
        strategy_data['total_profit'] += profit

        # Adapt strategy parameters if needed
        success_rate = strategy_data['successful_trades'] / strategy_data['total_trades']
        if success_rate < 0.3 and strategy_data['total_trades'] > 10:  # Low success rate after 10 trades
            if strategy_data['name'] in ['rsi_sma', 'atr_cci']:
                # Adjust thresholds
                base_low = strategy_data['parameters'].get('base_low', -100 if strategy_data['name'] == 'atr_cci' else 40)
                base_high = strategy_data['parameters'].get('base_high', 100 if strategy_data['name'] == 'atr_cci' else 60)
                strategy_data['parameters']['base_low'] = base_low * 1.1  # Widen the range
                strategy_data['parameters']['base_high'] = base_high * 0.9
                logger.info(f"Adjusted parameters for {strategy_data['name']} on {symbol}: base_low={strategy_data['parameters']['base_low']}, base_high={strategy_data['parameters']['base_high']}")
            elif strategy_data['name'] == 'bollinger':
                # No parameters to adjust for Bollinger Bands, consider removing
                logger.warning(f"Strategy {strategy_data['name']} on {symbol} has low success rate ({success_rate}), consider removing")
                strategy_data['disabled'] = True
            elif 'indicators' in strategy_data:  # Custom strategy
                # Mark custom strategy as disabled
                logger.warning(f"Custom strategy {strategy_data['indicators']} on {symbol} has low success rate ({success_rate}), disabling")
                strategy_data['disabled'] = True

        await redis_client.set(strategy_key, json.dumps(strategy_data), ex=86400 * 30)

        # Update custom strategies if needed
        if 'indicators' in strategy_data and strategy_data.get('disabled', False):
            custom_key = f"custom_strategies:{symbol}"
            custom_strategies = await redis_client.get(custom_key)
            if custom_strategies:
                custom_strategies = json.loads(custom_strategies.decode())
                custom_strategies = [s for s in custom_strategies if s['indicators'] != strategy_data['indicators']]
                await redis_client.set(custom_key, json.dumps(custom_strategies), ex=86400 * 30)
                logger.info(f"Removed disabled custom strategy {strategy_data['indicators']} for {symbol}")
    except Exception as e:
        logger.error(f"Failed to evaluate trade for {symbol}: {type(e).__name__}: {str(e)}")
    finally:
        await redis_client.close()

async def get_strategy_success(strategy_name, symbol, user):
    """Возвращает статистику успешности стратегии."""
    redis_client = await get_redis_client()
    try:
        strategy_key = f"strategy_success:{strategy_name}:{symbol}:{user}"
        strategy_data = await redis_client.get(strategy_key)
        if strategy_data:
            return json.loads(strategy_data.decode())
        return None
    finally:
        await redis_client.close()
