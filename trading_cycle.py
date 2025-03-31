import asyncio
from logging_setup import logger_main
from bot_trading import run_trading_bot

class TradingCycle:
    """Manages trading cycles."""
    def __init__(self, exchange_id, user_id, symbols):
        self.exchange_id = exchange_id
        self.user_id = user_id
        self.symbols = symbols

    async def run_cycle(self, interval=60):
        """Runs a trading cycle at specified intervals."""
        try:
            while True:
                logger_main.info(f"Starting trading cycle for user {self.user_id} on {self.exchange_id}")
                tasks = [run_trading_bot(self.exchange_id, self.user_id, symbol) for symbol in self.symbols]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                successful = sum(1 for result in results if result is True)
                logger_main.info(f"Completed trading cycle: {successful} successful trades out of {len(self.symbols)}")
                await asyncio.sleep(interval)
        except Exception as e:
            logger_main.error(f"Error in trading cycle for user {self.user_id} on {self.exchange_id}: {e}")

__all__ = ['TradingCycle']
