import ccxt.async_support as ccxt
import asyncio

async def test_symbol():
    exchange = ccxt.mexc({'enableRateLimit': True})
    try:
        await exchange.load_markets()
        symbols = ['LYUM/USDT', 'RSR/USDT', 'SOL/USDT']
        for symbol in symbols:
            print(f'{symbol}: {symbol in exchange.symbols}')
    except Exception as e:
        print(f"Ошибка: {str(e)}")
    finally:
        await exchange.close()

if __name__ == "__main__":
    asyncio.run(test_symbol())
