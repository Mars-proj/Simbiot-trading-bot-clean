import pandas as pd
from logging_setup import logger_main
from exchange_factory import create_exchange
from exchange_utils import fetch_ticker
from ohlcv_fetcher import fetch_ohlcv
from symbol_handler import validate_symbol
from config_keys import SUPPORTED_EXCHANGES

async def analyze_token(exchange_id, user_id, token_symbol, testnet=False, timeframe='1h', limit=100):
    """Analyzes a token's market data, including volume and volatility."""
    try:
        # Validate inputs
        if exchange_id not in SUPPORTED_EXCHANGES:
            logger_main.error(f"Exchange {exchange_id} not supported")
            return None
        if not user_id or not isinstance(user_id, str):
            logger_main.error(f"Invalid user_id: {user_id}")
            return None
        if not await validate_symbol(exchange_id, user_id, token_symbol, testnet=testnet):
            logger_main.error(f"Invalid token symbol: {token_symbol}")
            return None

        # Create exchange instance
        exchange = create_exchange(exchange_id, user_id, testnet=testnet)
        if not exchange:
            logger_main.error(f"Failed to create exchange instance for {exchange_id}")
            return None

        # Fetch ticker data
        ticker = await fetch_ticker(exchange, token_symbol, exchange_id, user_id, testnet=testnet)
        if not ticker:
            logger_main.error(f"Failed to fetch ticker for {token_symbol} on {exchange_id}")
            return None

        # Fetch OHLCV data
        ohlcv = await fetch_ohlcv(exchange_id, token_symbol, user_id, timeframe=timeframe, limit=limit, testnet=testnet, as_dataframe=True)
        if ohlcv is None or len(ohlcv) == 0:
            logger_main.error(f"Failed to fetch OHLCV data for {token_symbol} on {exchange_id}")
            return None

        # Calculate metrics
        df = ohlcv
        average_volume = df['volume'].mean()
        returns = df['close'].pct_change()
        volatility = returns.std()

        analysis = {
            'token': token_symbol,
            'current_price': ticker['last'],
            'average_volume': average_volume,
            'volatility': volatility,
            'spread': ticker['ask'] - ticker['bid']
        }
        logger_main.info(f"Token analysis for {token_symbol} on {exchange_id}: {analysis}")
        return analysis
    except Exception as e:
        logger_main.error(f"Error analyzing token {token_symbol} on {exchange_id}: {e}")
        return None
    finally:
        await exchange.close()

__all__ = ['analyze_token']
