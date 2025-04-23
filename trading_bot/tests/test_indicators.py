"""
Tests for the indicators module.
"""
import os
import sys
import unittest
import pandas as pd
import numpy as np

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.indicators import add_ema_indicators, add_macd_indicators, add_atr_indicator, get_strategy_signals

class TestIndicators(unittest.TestCase):
    """
    Test case for the indicators module.
    """
    
    def setUp(self):
        """Create sample data for testing."""
        # Create a simple DataFrame with price data
        self.df = pd.DataFrame({
            'timestamp': pd.date_range(start='2023-01-01', periods=100, freq='15min'),
            'open': np.random.random(100) * 100 + 20000,
            'high': np.random.random(100) * 100 + 20050,
            'low': np.random.random(100) * 100 + 19950,
            'close': np.random.random(100) * 100 + 20000,
            'volume': np.random.random(100) * 100
        })
    
    def test_add_ema_indicators(self):
        """Test adding EMA indicators."""
        fast_period = 9
        slow_period = 21
        
        df_with_ema = add_ema_indicators(self.df, fast_period, slow_period)
        
        # Check if the indicator columns were added
        self.assertIn(f'ema_{fast_period}', df_with_ema.columns)
        self.assertIn(f'ema_{slow_period}', df_with_ema.columns)
        self.assertIn('ema_crossover', df_with_ema.columns)
        
        # Check if the values are numeric
        self.assertTrue(pd.api.types.is_numeric_dtype(df_with_ema[f'ema_{fast_period}']))
        self.assertTrue(pd.api.types.is_numeric_dtype(df_with_ema[f'ema_{slow_period}']))
        
        # Check if the crossover signals are as expected
        self.assertTrue(all(df_with_ema['ema_crossover'].isin([0, 1, -1])))
    
    def test_add_macd_indicators(self):
        """Test adding MACD indicators."""
        fast_period = 12
        slow_period = 26
        signal_period = 9
        
        df_with_macd = add_macd_indicators(self.df, fast_period, slow_period, signal_period)
        
        # Check if the indicator columns were added
        self.assertIn('macd', df_with_macd.columns)
        self.assertIn('macd_signal', df_with_macd.columns)
        self.assertIn('macd_diff', df_with_macd.columns)
        self.assertIn('macd_crossover', df_with_macd.columns)
        
        # Check if the values are numeric
        self.assertTrue(pd.api.types.is_numeric_dtype(df_with_macd['macd']))
        self.assertTrue(pd.api.types.is_numeric_dtype(df_with_macd['macd_signal']))
        self.assertTrue(pd.api.types.is_numeric_dtype(df_with_macd['macd_diff']))
        
        # Check if the crossover signals are as expected
        self.assertTrue(all(df_with_macd['macd_crossover'].isin([0, 1, -1])))
    
    def test_add_atr_indicator(self):
        """Test adding ATR indicator."""
        period = 14
        
        df_with_atr = add_atr_indicator(self.df, period)
        
        # Check if the ATR column was added
        self.assertIn('atr', df_with_atr.columns)
        
        # Check if the values are numeric and positive
        self.assertTrue(pd.api.types.is_numeric_dtype(df_with_atr['atr']))
        self.assertTrue(all(df_with_atr['atr'] >= 0))
    
    def test_get_strategy_signals(self):
        """Test generating strategy signals."""
        # First add the required indicators
        df = self.df.copy()
        df = add_ema_indicators(df, 9, 21)
        df = add_macd_indicators(df, 12, 26, 9)
        
        # Generate signals
        df_with_signals = get_strategy_signals(df)
        
        # Check if the signal column was added
        self.assertIn('signal', df_with_signals.columns)
        
        # Check if the signals are as expected
        self.assertTrue(all(df_with_signals['signal'].isin([0, 1, -1])))

if __name__ == '__main__':
    unittest.main() 