import asyncio
import redis.asyncio as redis
from json_handler import loads

async def check_all_trades():
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    try:
        trade_keys = await redis_client.keys("trade:*")
        print(f"Найдено {len(trade_keys)} сделок в Redis")
        
        user1_trades = []
        for key in trade_keys:
            trade_data = await redis_client.get(key)
            if trade_data:
                trade = loads(trade_data)
                if trade.get('user_id') == "USER1":
                    user1_trades.append(trade)
        
        if not user1_trades:
            print("Сделки для USER1 не найдены")
        else:
            print(f"Найдено {len(user1_trades)} сделок для USER1:")
            for trade in user1_trades:
                print(trade)
        
        # Разделяем открытые и закрытые позиции
        open_positions = [trade for trade in user1_trades if trade['side'] == 'buy' and trade['status'] in ['pending', 'executed', 'filled']]
        closed_positions = [trade for trade in user1_trades if trade['side'] == 'sell' or trade['status'] in ['successful', 'failed']]
        
        print("\nОткрытые позиции для USER1:")
        for pos in open_positions:
            print(pos)
        
        print("\nЗакрытые позиции для USER1:")
        for pos in closed_positions:
            print(pos)
        
        # Подсчитаем общее количество DEFI
        total_defi_bought = sum(trade['amount'] for trade in user1_trades if trade['symbol'] == 'DEFI/USDT' and trade['side'] == 'buy')
        total_defi_sold = sum(trade['amount'] for trade in user1_trades if trade['symbol'] == 'DEFI/USDT' and trade['side'] == 'sell')
        print(f"\nОбщее количество DEFI куплено: {total_defi_bought}")
        print(f"Общее количество DEFI продано: {total_defi_sold}")
        print(f"Текущий баланс DEFI (куплено - продано): {total_defi_bought - total_defi_sold}")
        
    except Exception as e:
        print(f"Ошибка: {str(e)}")
    finally:
        await redis_client.close()

if __name__ == "__main__":
    asyncio.run(check_all_trades())
