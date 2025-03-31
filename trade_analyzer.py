import pandas as pd
from logging_setup import logger_main

def analyze_trades(trades):
    """Analyzes trades and calculates metrics."""
    try:
        df = pd.DataFrame(trades)
        if df.empty:
            logger_main.warning("No trades to analyze")
            return {}

        # Basic metrics
        total_trades = len(df)
        average_profit = df['profit'].mean() if 'profit' in df else 0
        max_drawdown = (df['profit'].cumsum().cummax() - df['profit'].cumsum()).max() if 'profit' in df else 0
        win_rate = len(df[df['profit'] > 0]) / total_trades if 'profit' in df and total_trades > 0 else 0

        metrics = {
            'total_trades': total_trades,
            'average_profit': average_profit,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate
        }

        logger_main.info(f"Analyzed trades: {metrics}")
        return metrics
    except Exception as e:
        logger_main.error(f"Error analyzing trades: {e}")
        return {}

__all__ = ['analyze_trades']
