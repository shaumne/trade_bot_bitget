"""
Backtesting module for the trading strategy.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
import ccxt
import logging

from src import config
from src.indicators import add_ema_indicators, add_macd_indicators, add_atr_indicator, get_strategy_signals

# Configure logging
logger = logging.getLogger(__name__)

class Backtester:
    """
    Backtesting class for the EMA + MACD strategy.
    """
    
    def __init__(self, start_date=None, end_date=None):
        """
        Initialize the backtester.
        
        Args:
            start_date (str, optional): Start date for backtesting (YYYY-MM-DD)
            end_date (str, optional): End date for backtesting (YYYY-MM-DD)
        """
        self.symbol = config.SYMBOL
        self.timeframe = config.TIMEFRAME
        
        # Use config dates if not specified
        self.start_date = start_date or config.BACKTEST_START_DATE
        self.end_date = end_date or config.BACKTEST_END_DATE
        
        # Convert dates to datetime objects
        if self.start_date:
            self.start_date = datetime.strptime(self.start_date, "%Y-%m-%d")
        if self.end_date:
            self.end_date = datetime.strptime(self.end_date, "%Y-%m-%d")
        
        # Initialize exchange for historical data
        self.exchange = ccxt.bitget({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',
            }
        })
        
        # Strategy parameters
        self.ema_fast = config.EMA_FAST
        self.ema_slow = config.EMA_SLOW
        self.macd_fast = config.MACD_FAST
        self.macd_slow = config.MACD_SLOW
        self.macd_signal = config.MACD_SIGNAL
        self.atr_period = config.ATR_PERIOD
        
        # Risk management
        self.stop_loss_atr = config.STOP_LOSS_ATR_MULTIPLIER
        self.take_profit1_atr = config.TAKE_PROFIT1_ATR_MULTIPLIER
        self.take_profit2_atr = config.TAKE_PROFIT2_ATR_MULTIPLIER
        self.risk_per_trade = config.RISK_PER_TRADE
        self.max_positions = config.MAX_POSITIONS
        self.max_trades_per_day = config.MAX_TRADES_PER_DAY
    
    def fetch_historical_data(self):
        """
        Fetch historical data for backtesting.
        
        Returns:
            pandas.DataFrame: Historical OHLCV data
        """
        # Convert timeframe string to milliseconds for CCXT
        timeframes = {
            '1m': 60 * 1000,
            '5m': 5 * 60 * 1000,
            '15m': 15 * 60 * 1000,
            '1h': 60 * 60 * 1000,
            '4h': 4 * 60 * 60 * 1000,
            '1d': 24 * 60 * 60 * 1000
        }
        
        # Calculate time ranges
        if self.start_date and self.end_date:
            start_timestamp = int(self.start_date.timestamp() * 1000)
            end_timestamp = int(self.end_date.timestamp() * 1000)
        else:
            # Default to last 30 days if no dates specified
            end_timestamp = int(datetime.now().timestamp() * 1000)
            start_timestamp = end_timestamp - (30 * 24 * 60 * 60 * 1000)  # 30 days
        
        # Fetch data in chunks due to exchange limits
        all_candles = []
        current_timestamp = start_timestamp
        
        while current_timestamp < end_timestamp:
            try:
                candles = self.exchange.fetch_ohlcv(
                    symbol=self.symbol,
                    timeframe=self.timeframe,
                    since=current_timestamp,
                    limit=1000  # Maximum allowed by most exchanges
                )
                
                if not candles:
                    break
                
                all_candles.extend(candles)
                
                # Update timestamp for next batch
                current_timestamp = candles[-1][0] + timeframes[self.timeframe]
                
            except Exception as e:
                logger.error(f"Error fetching historical data: {e}")
                break
        
        # Convert to DataFrame
        df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        return df
    
    def prepare_data(self, df):
        """
        Prepare data with indicators for backtesting.
        
        Args:
            df (pandas.DataFrame): Historical OHLCV data
            
        Returns:
            pandas.DataFrame: Data with indicators
        """
        # Reset index for indicator calculations
        df = df.reset_index()
        
        # Add indicators
        df = add_ema_indicators(df, self.ema_fast, self.ema_slow)
        df = add_macd_indicators(df, self.macd_fast, self.macd_slow, self.macd_signal)
        df = add_atr_indicator(df, self.atr_period)
        
        # Generate strategy signals
        df = get_strategy_signals(df)
        
        return df
    
    def run_backtest(self):
        """
        Run the backtest.
        
        Returns:
            tuple: (DataFrame with trades, performance metrics)
        """
        # Fetch and prepare data
        df = self.fetch_historical_data()
        df = self.prepare_data(df)
        
        # Initialize variables
        initial_balance = 10000  # Starting with $10,000
        balance = initial_balance
        position = None
        position_size = 0
        entry_price = 0
        stop_loss = 0
        take_profit1 = 0
        take_profit2 = 0
        trade_count = 0
        winning_trades = 0
        losing_trades = 0
        total_profit = 0
        total_loss = 0
        trades = []
        equity_curve = [initial_balance]
        
        # Track daily trade count
        current_date = None
        trades_today = 0
        
        # Run backtest
        for i in range(1, len(df)):
            current_row = df.iloc[i]
            prev_row = df.iloc[i-1]
            
            # Reset daily trade count
            if current_date != current_row['timestamp'].date():
                current_date = current_row['timestamp'].date()
                trades_today = 0
            
            # Process open positions
            if position:
                # Check for stop loss
                if position == 'long' and current_row['low'] <= stop_loss:
                    # Stop loss hit
                    profit = (stop_loss - entry_price) / entry_price * position_size
                    balance += profit
                    total_loss += abs(profit) if profit < 0 else 0
                    losing_trades += 1
                    trades.append({
                        'type': 'close_long',
                        'reason': 'stop_loss',
                        'entry_time': prev_row['timestamp'],
                        'exit_time': current_row['timestamp'],
                        'entry_price': entry_price,
                        'exit_price': stop_loss,
                        'position_size': position_size,
                        'profit': profit,
                        'balance': balance
                    })
                    position = None
                    equity_curve.append(balance)
                
                elif position == 'short' and current_row['high'] >= stop_loss:
                    # Stop loss hit
                    profit = (entry_price - stop_loss) / entry_price * position_size
                    balance += profit
                    total_loss += abs(profit) if profit < 0 else 0
                    losing_trades += 1
                    trades.append({
                        'type': 'close_short',
                        'reason': 'stop_loss',
                        'entry_time': prev_row['timestamp'],
                        'exit_time': current_row['timestamp'],
                        'entry_price': entry_price,
                        'exit_price': stop_loss,
                        'position_size': position_size,
                        'profit': profit,
                        'balance': balance
                    })
                    position = None
                    equity_curve.append(balance)
                
                # Check for take profit 1 (half position)
                elif position == 'long' and current_row['high'] >= take_profit1:
                    # Take profit 1 hit (close half position)
                    half_position = position_size * 0.5
                    profit = (take_profit1 - entry_price) / entry_price * half_position
                    balance += profit
                    total_profit += profit if profit > 0 else 0
                    winning_trades += 0.5  # Count as half a winning trade
                    trades.append({
                        'type': 'partial_close_long',
                        'reason': 'take_profit1',
                        'entry_time': prev_row['timestamp'],
                        'exit_time': current_row['timestamp'],
                        'entry_price': entry_price,
                        'exit_price': take_profit1,
                        'position_size': half_position,
                        'profit': profit,
                        'balance': balance
                    })
                    position_size = half_position  # Reduce position size
                    equity_curve.append(balance)
                
                elif position == 'short' and current_row['low'] <= take_profit1:
                    # Take profit 1 hit (close half position)
                    half_position = position_size * 0.5
                    profit = (entry_price - take_profit1) / entry_price * half_position
                    balance += profit
                    total_profit += profit if profit > 0 else 0
                    winning_trades += 0.5  # Count as half a winning trade
                    trades.append({
                        'type': 'partial_close_short',
                        'reason': 'take_profit1',
                        'entry_time': prev_row['timestamp'],
                        'exit_time': current_row['timestamp'],
                        'entry_price': entry_price,
                        'exit_price': take_profit1,
                        'position_size': half_position,
                        'profit': profit,
                        'balance': balance
                    })
                    position_size = half_position  # Reduce position size
                    equity_curve.append(balance)
                
                # Check for take profit 2 (remaining position)
                elif position == 'long' and position_size > 0 and current_row['high'] >= take_profit2:
                    # Take profit 2 hit (close remaining position)
                    profit = (take_profit2 - entry_price) / entry_price * position_size
                    balance += profit
                    total_profit += profit if profit > 0 else 0
                    winning_trades += 0.5  # Count as half a winning trade
                    trades.append({
                        'type': 'close_long',
                        'reason': 'take_profit2',
                        'entry_time': prev_row['timestamp'],
                        'exit_time': current_row['timestamp'],
                        'entry_price': entry_price,
                        'exit_price': take_profit2,
                        'position_size': position_size,
                        'profit': profit,
                        'balance': balance
                    })
                    position = None
                    equity_curve.append(balance)
                
                elif position == 'short' and position_size > 0 and current_row['low'] <= take_profit2:
                    # Take profit 2 hit (close remaining position)
                    profit = (entry_price - take_profit2) / entry_price * position_size
                    balance += profit
                    total_profit += profit if profit > 0 else 0
                    winning_trades += 0.5  # Count as half a winning trade
                    trades.append({
                        'type': 'close_short',
                        'reason': 'take_profit2',
                        'entry_time': prev_row['timestamp'],
                        'exit_time': current_row['timestamp'],
                        'entry_price': entry_price,
                        'exit_price': take_profit2,
                        'position_size': position_size,
                        'profit': profit,
                        'balance': balance
                    })
                    position = None
                    equity_curve.append(balance)
                
                # Check for exit based on strategy signal
                elif position == 'long' and current_row['ema_crossover'] == -1 and current_row['macd_crossover'] == -1:
                    # Exit long on bearish crossover
                    current_price = current_row['close']
                    profit = (current_price - entry_price) / entry_price * position_size
                    balance += profit
                    if profit > 0:
                        total_profit += profit
                        winning_trades += 1
                    else:
                        total_loss += abs(profit)
                        losing_trades += 1
                    trades.append({
                        'type': 'close_long',
                        'reason': 'signal',
                        'entry_time': prev_row['timestamp'],
                        'exit_time': current_row['timestamp'],
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'position_size': position_size,
                        'profit': profit,
                        'balance': balance
                    })
                    position = None
                    equity_curve.append(balance)
                
                elif position == 'short' and current_row['ema_crossover'] == 1 and current_row['macd_crossover'] == 1:
                    # Exit short on bullish crossover
                    current_price = current_row['close']
                    profit = (entry_price - current_price) / entry_price * position_size
                    balance += profit
                    if profit > 0:
                        total_profit += profit
                        winning_trades += 1
                    else:
                        total_loss += abs(profit)
                        losing_trades += 1
                    trades.append({
                        'type': 'close_short',
                        'reason': 'signal',
                        'entry_time': prev_row['timestamp'],
                        'exit_time': current_row['timestamp'],
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'position_size': position_size,
                        'profit': profit,
                        'balance': balance
                    })
                    position = None
                    equity_curve.append(balance)
            
            # Look for new signals
            elif trades_today < self.max_trades_per_day:
                if current_row['signal'] == 1:  # Long signal
                    # Open long position
                    entry_price = current_row['close']
                    atr_value = current_row['atr']
                    stop_loss = entry_price - (atr_value * self.stop_loss_atr)
                    take_profit1 = entry_price + (atr_value * self.take_profit1_atr)
                    take_profit2 = entry_price + (atr_value * self.take_profit2_atr)
                    risk_amount = balance * self.risk_per_trade
                    position_size = risk_amount  # Simplified position sizing
                    position = 'long'
                    trade_count += 1
                    trades_today += 1
                    trades.append({
                        'type': 'open_long',
                        'entry_time': current_row['timestamp'],
                        'entry_price': entry_price,
                        'position_size': position_size,
                        'stop_loss': stop_loss,
                        'take_profit1': take_profit1,
                        'take_profit2': take_profit2
                    })
                
                elif current_row['signal'] == -1:  # Short signal
                    # Open short position
                    entry_price = current_row['close']
                    atr_value = current_row['atr']
                    stop_loss = entry_price + (atr_value * self.stop_loss_atr)
                    take_profit1 = entry_price - (atr_value * self.take_profit1_atr)
                    take_profit2 = entry_price - (atr_value * self.take_profit2_atr)
                    risk_amount = balance * self.risk_per_trade
                    position_size = risk_amount  # Simplified position sizing
                    position = 'short'
                    trade_count += 1
                    trades_today += 1
                    trades.append({
                        'type': 'open_short',
                        'entry_time': current_row['timestamp'],
                        'entry_price': entry_price,
                        'position_size': position_size,
                        'stop_loss': stop_loss,
                        'take_profit1': take_profit1,
                        'take_profit2': take_profit2
                    })
        
        # Close any remaining positions at the end
        if position:
            current_price = df.iloc[-1]['close']
            if position == 'long':
                profit = (current_price - entry_price) / entry_price * position_size
            else:
                profit = (entry_price - current_price) / entry_price * position_size
            
            balance += profit
            if profit > 0:
                total_profit += profit
                winning_trades += 1
            else:
                total_loss += abs(profit)
                losing_trades += 1
            
            trades.append({
                'type': f'close_{position}',
                'reason': 'end_of_backtest',
                'entry_time': df.iloc[-2]['timestamp'],
                'exit_time': df.iloc[-1]['timestamp'],
                'entry_price': entry_price,
                'exit_price': current_price,
                'position_size': position_size,
                'profit': profit,
                'balance': balance
            })
            equity_curve.append(balance)
        
        # Calculate performance metrics
        total_trades = trade_count
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        net_profit = balance - initial_balance
        percent_return = (net_profit / initial_balance) * 100
        
        metrics = {
            'initial_balance': initial_balance,
            'final_balance': balance,
            'net_profit': net_profit,
            'percent_return': percent_return,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_profit': total_profit,
            'total_loss': total_loss
        }
        
        # Convert trades to DataFrame for analysis
        trades_df = pd.DataFrame(trades)
        
        # Create equity curve DataFrame
        equity_df = pd.DataFrame({'equity': equity_curve})
        
        return trades_df, metrics, equity_df
    
    def plot_results(self, trades_df, metrics, equity_df):
        """
        Plot backtest results.
        
        Args:
            trades_df (pandas.DataFrame): DataFrame with trade information
            metrics (dict): Performance metrics
            equity_df (pandas.DataFrame): Equity curve data
        """
        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backtest_results')
        os.makedirs(output_dir, exist_ok=True)
        
        # Plot equity curve
        plt.figure(figsize=(12, 6))
        plt.plot(equity_df.index, equity_df['equity'])
        plt.title('Equity Curve')
        plt.xlabel('Trade Number')
        plt.ylabel('Account Balance')
        plt.grid(True)
        plt.savefig(os.path.join(output_dir, 'equity_curve.png'))
        
        # Plot trade outcomes
        if 'profit' in trades_df.columns:
            profit_df = trades_df[trades_df['type'].str.startswith('close')].copy()
            if not profit_df.empty:
                plt.figure(figsize=(12, 6))
                profit_df['profit'].plot(kind='bar')
                plt.title('Trade Outcomes')
                plt.xlabel('Trade Number')
                plt.ylabel('Profit/Loss')
                plt.axhline(y=0, color='r', linestyle='-')
                plt.grid(True)
                plt.savefig(os.path.join(output_dir, 'trade_outcomes.png'))
        
        # Save metrics to file
        with open(os.path.join(output_dir, 'metrics.txt'), 'w') as f:
            f.write("Backtest Results\n")
            f.write("===============\n\n")
            f.write(f"Symbol: {self.symbol}\n")
            f.write(f"Timeframe: {self.timeframe}\n")
            f.write(f"Period: {self.start_date} to {self.end_date}\n\n")
            f.write(f"Initial Balance: ${metrics['initial_balance']:.2f}\n")
            f.write(f"Final Balance: ${metrics['final_balance']:.2f}\n")
            f.write(f"Net Profit: ${metrics['net_profit']:.2f}\n")
            f.write(f"Percent Return: {metrics['percent_return']:.2f}%\n\n")
            f.write(f"Total Trades: {metrics['total_trades']}\n")
            f.write(f"Winning Trades: {metrics['winning_trades']}\n")
            f.write(f"Losing Trades: {metrics['losing_trades']}\n")
            f.write(f"Win Rate: {metrics['win_rate']*100:.2f}%\n")
            f.write(f"Profit Factor: {metrics['profit_factor']:.2f}\n\n")
            f.write(f"Total Profit: ${metrics['total_profit']:.2f}\n")
            f.write(f"Total Loss: ${metrics['total_loss']:.2f}\n")
        
        # Save trades to CSV
        trades_df.to_csv(os.path.join(output_dir, 'trades.csv'), index=False)
        
        logger.info(f"Backtest results saved to {output_dir}")
    
    def run(self):
        """
        Run the backtest and plot results.
        """
        logger.info(f"Starting backtest for {self.symbol} on {self.timeframe} timeframe")
        logger.info(f"Period: {self.start_date} to {self.end_date}")
        
        try:
            trades_df, metrics, equity_df = self.run_backtest()
            self.plot_results(trades_df, metrics, equity_df)
            
            logger.info("Backtest completed successfully")
            logger.info(f"Net Profit: ${metrics['net_profit']:.2f} ({metrics['percent_return']:.2f}%)")
            logger.info(f"Win Rate: {metrics['win_rate']*100:.2f}%")
            
            return metrics
        
        except Exception as e:
            logger.error(f"Error during backtesting: {e}")
            raise 