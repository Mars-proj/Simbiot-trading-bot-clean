import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

def calculate_volatility(df, window=20):
    """
    Calculate the rolling volatility (standard deviation) of the closing price.

    Args:
        df: DataFrame with OHLCV data (columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume']).
        window: Rolling window size for volatility calculation (default: 20).

    Returns:
        Series: Rolling volatility.
    """
    returns = df['close'].pct_change()
    volatility = returns.rolling(window=window).std() * np.sqrt(window)
    return volatility

def extract_features(df):
    """
    Extract features from OHLCV data for machine learning.

    Args:
        df: DataFrame with OHLCV data (columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume']).

    Returns:
        DataFrame: DataFrame with additional features.
    """
    df = df.copy()
    
    # Calculate basic features
    df['returns'] = df['close'].pct_change()
    df['volatility'] = calculate_volatility(df)
    
    # Moving averages
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    
    # RSI (Relative Strength Index)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD (Moving Average Convergence Divergence)
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    # Drop NaN values
    df = df.dropna()
    return df

def normalize_data(df, columns=None):
    """
    Normalize specified columns in the DataFrame using Min-Max Scaling.

    Args:
        df: DataFrame with data to normalize.
        columns: List of column names to normalize. If None, all numeric columns are normalized.

    Returns:
        DataFrame: DataFrame with normalized columns.
    """
    df = df.copy()
    
    # If columns are not specified, select all numeric columns
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Initialize the scaler
    scaler = MinMaxScaler()
    
    # Normalize the specified columns
    df[columns] = scaler.fit_transform(df[columns])
    
    return df
