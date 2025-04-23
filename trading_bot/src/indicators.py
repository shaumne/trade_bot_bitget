"""
Technical indicators for the trading strategy.
Includes EMA and MACD calculations for signal generation.
"""
import numpy as np
import pandas as pd
from ta.trend import EMAIndicator, MACD
from ta.volatility import AverageTrueRange

def add_ema_indicators(df, fast_period, slow_period):
    """
    Add EMA indicators to the dataframe.
    
    Args:
        df (pandas.DataFrame): Price data with 'close' column
        fast_period (int): Fast EMA period
        slow_period (int): Slow EMA period
        
    Returns:
        pandas.DataFrame: DataFrame with added EMA indicators
    """
    # Calculate EMA values
    df[f'ema_{fast_period}'] = EMAIndicator(close=df['close'], window=fast_period, fillna=True).ema_indicator()
    df[f'ema_{slow_period}'] = EMAIndicator(close=df['close'], window=slow_period, fillna=True).ema_indicator()
    
    # Calculate crossover signals
    df['ema_crossover'] = 0
    
    # Bullish crossover (fast crosses above slow)
    bullish = (df[f'ema_{fast_period}'] > df[f'ema_{slow_period}']) & (df[f'ema_{fast_period}'].shift(1) <= df[f'ema_{slow_period}'].shift(1))
    
    # Bearish crossover (fast crosses below slow)
    bearish = (df[f'ema_{fast_period}'] < df[f'ema_{slow_period}']) & (df[f'ema_{fast_period}'].shift(1) >= df[f'ema_{slow_period}'].shift(1))
    
    df.loc[bullish, 'ema_crossover'] = 1   # Bullish signal
    df.loc[bearish, 'ema_crossover'] = -1  # Bearish signal
    
    return df

def add_macd_indicators(df, fast_period, slow_period, signal_period):
    """
    Add MACD indicators to the dataframe.
    
    Args:
        df (pandas.DataFrame): Price data with 'close' column
        fast_period (int): Fast MACD period
        slow_period (int): Slow MACD period
        signal_period (int): Signal line period
        
    Returns:
        pandas.DataFrame: DataFrame with added MACD indicators
    """
    # Calculate MACD
    macd_indicator = MACD(
        close=df['close'],
        window_fast=fast_period,
        window_slow=slow_period,
        window_sign=signal_period,
        fillna=True
    )
    
    df['macd'] = macd_indicator.macd()
    df['macd_signal'] = macd_indicator.macd_signal()
    df['macd_diff'] = macd_indicator.macd_diff()
    
    # Calculate crossover signals
    df['macd_crossover'] = 0
    
    # Bullish crossover (MACD crosses above signal line)
    bullish = (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1))
    
    # Bearish crossover (MACD crosses below signal line)
    bearish = (df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1))
    
    df.loc[bullish, 'macd_crossover'] = 1   # Bullish signal
    df.loc[bearish, 'macd_crossover'] = -1  # Bearish signal
    
    return df

def add_atr_indicator(df, period):
    """
    Add Average True Range (ATR) indicator to the dataframe.
    
    Args:
        df (pandas.DataFrame): Price data with 'high', 'low', 'close' columns
        period (int): ATR period
        
    Returns:
        pandas.DataFrame: DataFrame with added ATR indicator
    """
    df['atr'] = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=period, fillna=True).average_true_range()
    return df

def get_strategy_signals(df):
    """
    Generate strategy signals based on EMA and MACD crossovers.
    
    Args:
        df (pandas.DataFrame): DataFrame with calculated indicators
        
    Returns:
        pandas.DataFrame: DataFrame with strategy signals
    """
    # Initialize signal column
    df['signal'] = 0
    
    # Long signal: EMA bullish crossover AND MACD bullish crossover
    # Geliştirilmiş versiyon: Son 3 mum içinde her iki sinyal de bullish olduğunda
    ema_bullish_recent = df['ema_crossover'].rolling(window=3).sum() > 0
    macd_bullish_recent = df['macd_crossover'].rolling(window=3).sum() > 0
    long_condition = ema_bullish_recent & macd_bullish_recent
    
    # Short signal: EMA bearish crossover AND MACD bearish crossover
    # Geliştirilmiş versiyon: Son 3 mum içinde her iki sinyal de bearish olduğunda
    ema_bearish_recent = df['ema_crossover'].rolling(window=3).sum() < 0
    macd_bearish_recent = df['macd_crossover'].rolling(window=3).sum() < 0
    short_condition = ema_bearish_recent & macd_bearish_recent
    
    # Exit long: EMA bearish crossover AND MACD bearish crossover
    exit_long_condition = (df['ema_crossover'] == -1) & (df['macd_crossover'] == -1)
    
    # Exit short: EMA bullish crossover AND MACD bullish crossover
    exit_short_condition = (df['ema_crossover'] == 1) & (df['macd_crossover'] == 1)
    
    # Set signals
    df.loc[long_condition, 'signal'] = 1
    df.loc[short_condition, 'signal'] = -1
    
    return df 