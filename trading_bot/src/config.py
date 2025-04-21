"""
Configuration module for the trading bot.
Loads and validates all settings from the .env file.
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parents[1] / '.env'
load_dotenv(dotenv_path=env_path)

# Bitget API credentials
API_KEY = os.getenv('BITGET_API_KEY')
API_SECRET = os.getenv('BITGET_API_SECRET')
API_PASSPHRASE = os.getenv('BITGET_API_PASSPHRASE')

# Trading parameters
SYMBOL = os.getenv('SYMBOL', 'BTCUSDT')
LEVERAGE = int(os.getenv('LEVERAGE', '1'))
TIMEFRAME = os.getenv('TIMEFRAME', '15m')

# Strategy parameters
EMA_FAST = int(os.getenv('EMA_FAST', '9'))
EMA_SLOW = int(os.getenv('EMA_SLOW', '21'))
MACD_FAST = int(os.getenv('MACD_FAST', '12'))
MACD_SLOW = int(os.getenv('MACD_SLOW', '26'))
MACD_SIGNAL = int(os.getenv('MACD_SIGNAL', '9'))

# Risk management
RISK_PER_TRADE = float(os.getenv('RISK_PER_TRADE', '0.5'))
MAX_POSITIONS = int(os.getenv('MAX_POSITIONS', '2'))
MAX_TRADES_PER_DAY = int(os.getenv('MAX_TRADES_PER_DAY', '6'))
STOP_LOSS_ATR_MULTIPLIER = float(os.getenv('STOP_LOSS_ATR_MULTIPLIER', '2'))
TAKE_PROFIT1_ATR_MULTIPLIER = float(os.getenv('TAKE_PROFIT1_ATR_MULTIPLIER', '3'))
TAKE_PROFIT2_ATR_MULTIPLIER = float(os.getenv('TAKE_PROFIT2_ATR_MULTIPLIER', '5'))
ATR_PERIOD = int(os.getenv('ATR_PERIOD', '14'))

# Notification settings
EMAIL_RECIPIENT = os.getenv('EMAIL_RECIPIENT')
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Backtesting
BACKTEST_START_DATE = os.getenv('BACKTEST_START_DATE')
BACKTEST_END_DATE = os.getenv('BACKTEST_END_DATE')

# Validate essential configuration
def validate_config():
    """Validates that essential configuration items are present."""
    essential_configs = [
        ('API_KEY', API_KEY),
        ('API_SECRET', API_SECRET),
        ('API_PASSPHRASE', API_PASSPHRASE),
        ('SYMBOL', SYMBOL),
    ]
    
    missing_configs = [name for name, value in essential_configs if not value]
    
    if missing_configs:
        raise ValueError(f"Missing essential configuration: {', '.join(missing_configs)}")
        
    return True 