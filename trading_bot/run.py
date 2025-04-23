#!/usr/bin/env python
"""
Simple entry point script for running the trading bot.
"""
import os
import sys
import argparse

from main import run_trading_bot, validate_environment

def parse_args():
    parser = argparse.ArgumentParser(description='Run trading bot with configurable interval')
    parser.add_argument('--interval', type=int, default=15,
                      help='Interval between trading iterations in seconds (default: 15)')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    if validate_environment():
        run_trading_bot(interval=args.interval)
    else:
        print("Environment validation failed. Check logs for details.") 