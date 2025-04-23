#!/usr/bin/env python
"""
Main entry point for the trading bot.
"""
import os
import sys
import logging
import time
import argparse
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import config
from src.trader import TradingBot
from src.backtest import Backtester

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f'trading_bot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

logging.basicConfig(
    level=logging.getLevelName(config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def validate_environment():
    """
    Validate that all required environment variables are set.
    """
    try:
        config.validate_config()
        logger.info("Configuration validated successfully")
        return True
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        return False

def run_trading_bot(interval=5):
    """
    Run the trading bot.
    
    Args:
        interval (int): Interval between trading iterations in seconds
    """
    if not validate_environment():
        logger.error("Cannot start trading bot due to invalid configuration")
        return
    
    logger.info(f"Starting trading bot with {interval} second interval")
    
    # Initialize and run the trading bot
    bot = TradingBot()
    bot.run(interval=interval)

def run_backtest(start_date=None, end_date=None):
    """
    Run a backtest of the trading strategy.
    
    Args:
        start_date (str, optional): Start date for backtesting (YYYY-MM-DD)
        end_date (str, optional): End date for backtesting (YYYY-MM-DD)
    """
    logger.info("Starting backtest")
    
    # Initialize and run the backtester
    backtester = Backtester(start_date, end_date)
    results = backtester.run()
    
    logger.info("Backtest completed")
    return results

def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Bitget Trading Bot')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Trading bot command
    trade_parser = subparsers.add_parser('trade', help='Run the trading bot')
    trade_parser.add_argument('--interval', type=int, default=5,
                             help='Interval between trading iterations in seconds (default: 30)')
    
    # Backtest command
    backtest_parser = subparsers.add_parser('backtest', help='Run a backtest of the trading strategy')
    backtest_parser.add_argument('--start-date', type=str,
                                help='Start date for backtesting (YYYY-MM-DD)')
    backtest_parser.add_argument('--end-date', type=str,
                                help='End date for backtesting (YYYY-MM-DD)')
    
    return parser.parse_args()

def main():
    """
    Main entry point.
    """
    try:
        args = parse_arguments()
        
        if args.command == 'trade':
            run_trading_bot(interval=args.interval)
        elif args.command == 'backtest':
            run_backtest(start_date=args.start_date, end_date=args.end_date)
        else:
            logger.error("No command specified. Use 'trade' or 'backtest'")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Program stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main() 