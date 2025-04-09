# learning/trade_evaluator.py
import logging
import redis.asyncio as redis
import json
import numpy as np

logger = logging.getLogger("main")

async def get_redis_client():
    return await redis.from_url("redis://localhost:6379/0")

async def evaluate_trade(symbol, user, strategy_info, profit):
    redis_client = await get_redis_client()
    try:
        trade_key = f"trade_history:{symbol}:{user}"
        profit_key = f"profitability:{symbol}"

        # Сохраняем историю сделки
        trade_data = {
            "strategy": strategy_info,
            "profit": profit,
            "timestamp": int(time.time())
        }
        await redis_client.lpush(trade_key, json.dumps(trade_data))

        # Обновляем статистику прибыльности
        profit_data = await redis_client.get(profit_key)
        if profit_data:
            profit_data = json.loads(profit_data.decode())
        else:
            profit_data = {
                "total_trades": 0,
                "successful_trades": 0,
                "success_rate": 0.5,
                "avg_profit": 0.0,
                "profit_volatility": 0.0,
                "profits": []
            }

        profit_data["total_trades"] += 1
        if profit > 0:
            profit_data["successful_trades"] += 1
        profit_data["success_rate"] = profit_data["successful_trades"] / profit_data["total_trades"]
        profit_data["profits"].append(profit)
        if len(profit_data["profits"]) > 100:  # Ограничиваем историю до 100 сделок
            profit_data["profits"] = profit_data["profits"][-100:]
        profit_data["avg_profit"] = np.mean(profit_data["profits"])
        profit_data["profit_volatility"] = np.std(profit_data["profits"]) if len(profit_data["profits"]) > 1 else 0.0

        await redis_client.set(profit_key, json.dumps(profit_data), ex=86400 * 30)
        logger.info(f"Evaluated trade for {symbol}: profit={profit}, success_rate={profit_data['success_rate']:.2f}, avg_profit={profit_data['avg_profit']:.2f}, profit_volatility={profit_data['profit_volatility']:.2f}")
    except Exception as e:
        logger.error(f"Failed to evaluate trade for {symbol}: {type(e).__name__}: {str(e)}")
    finally:
        await redis_client.close()
