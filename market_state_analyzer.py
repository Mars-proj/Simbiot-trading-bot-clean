# market_state_analyzer.py
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger("main")

async def analyze_market_state(exchange_pool, timeframe='4h'):
    try:
        logger.debug("Fetching markets")
        markets = exchange_pool.get_markets()
        if not markets:
            logger.error("No markets available, using default market state")
            return {'trend': 'neutral', 'volatility': 0.01, 'market_type': 'sideways'}, []

        symbols = [symbol for symbol in markets.keys() if symbol.endswith('/USDT')]
        if not symbols:
            logger.error("No USDT symbols available, using default market state")
            return {'trend': 'neutral', 'volatility': 0.01, 'market_type': 'sideways'}, []

        logger.debug(f"Analyzing market state with {len(symbols)} symbols")
        total_volatility = 0
        trend_scores = {'up': 0, 'down': 0, 'neutral': 0}
        for symbol in symbols[:10]:  # Ограничиваем анализ первыми 10 символами
            try:
                ohlcv = await exchange_pool.fetch_ohlcv(symbol, timeframe, limit=100)
                if not ohlcv or len(ohlcv) < 2:
                    logger.warning(f"Insufficient OHLCV data for {symbol}, skipping")
                    continue

                closes = [candle[4] for candle in ohlcv]
                df = pd.Series(closes)
                returns = df.pct_change().dropna()
                volatility = returns.std() * np.sqrt(24 * 365)
                total_volatility += volatility if not np.isnan(volatility) else 0

                short_sma = df.rolling(window=10).mean().iloc[-1]
                long_sma = df.rolling(window=20).mean().iloc[-1]
                if short_sma > long_sma:
                    trend_scores['up'] += 1
                elif short_sma < long_sma:
                    trend_scores['down'] += 1
                else:
                    trend_scores['neutral'] += 1
            except Exception as e:
                logger.error(f"Failed to analyze {symbol}: {type(e).__name__}: {str(e)}")
                continue

        if not trend_scores['up'] and not trend_scores['down'] and not trend_scores['neutral']:
            logger.error("No valid data for market analysis, using default market state")
            return {'trend': 'neutral', 'volatility': 0.01, 'market_type': 'sideways'}, []

        avg_volatility = total_volatility / (trend_scores['up'] + trend_scores['down'] + trend_scores['neutral'])
        dominant_trend = max(trend_scores, key=trend_scores.get)

        market_type = 'sideways'
        if avg_volatility > 0.5:
            market_type = 'volatile'
        elif dominant_trend in ['up', 'down']:
            market_type = 'trending'

        market_state = {
            'trend': dominant_trend,
            'volatility': avg_volatility,
            'market_type': market_type
        }
        return market_state, symbols
    except Exception as e:
        logger.error(f"Failed to analyze market state: {type(e).__name__}: {str(e)}")
        return {'trend': 'neutral', 'volatility': 0.01, 'market_type': 'sideways'}, []
