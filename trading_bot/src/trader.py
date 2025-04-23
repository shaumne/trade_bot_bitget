"""
Main trader module that implements the EMA + MACD crossover trading strategy.
"""
import time
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src import config
from src.exchange import BitgetExchange
from src.indicators import add_ema_indicators, add_macd_indicators, add_atr_indicator, get_strategy_signals
from src.notifications import EmailNotifier

# Configure logging
logger = logging.getLogger(__name__)

class TradingBot:
    """
    Main trading bot class that implements the strategy.
    """
    
    def __init__(self):
        """Initialize the trading bot."""
        self.exchange = BitgetExchange()
        self.notifier = EmailNotifier()
        self.symbol = config.SYMBOL
        self.timeframe = config.TIMEFRAME
        self.trades_today = 0
        self.last_trade_reset = datetime.now().date()
        self.open_positions = []
        self.trade_log = []
    
    def reset_daily_trade_count(self):
        """Reset the daily trade count if it's a new day."""
        today = datetime.now().date()
        if today > self.last_trade_reset:
            self.trades_today = 0
            self.last_trade_reset = today
            logger.info(f"Reset daily trade count on {today}")
    
    def get_market_data(self, limit=100):
        """
        Fetch market data and calculate indicators.
        
        Args:
            limit (int): Number of candles to fetch
            
        Returns:
            pandas.DataFrame: Market data with indicators
        """
        # Fetch OHLCV data
        df = self.exchange.fetch_ohlcv(limit=limit)
        
        # Add indicators
        df = add_ema_indicators(df, config.EMA_FAST, config.EMA_SLOW)
        df = add_macd_indicators(df, config.MACD_FAST, config.MACD_SLOW, config.MACD_SIGNAL)
        df = add_atr_indicator(df, config.ATR_PERIOD)
        
        # Generate strategy signals
        df = get_strategy_signals(df)
        
        return df
    
    def check_open_positions(self):
        """
        Check and update the list of open positions.
        
        Returns:
            int: Number of open positions
        """
        positions = self.exchange.get_open_positions()
        self.open_positions = [p for p in positions if abs(float(p['info']['size'])) > 0]
        return len(self.open_positions)
    
    def can_open_new_trade(self):
        """
        Check if a new trade can be opened.
        
        Returns:
            bool: True if a new trade can be opened, False otherwise
        """
        # Reset daily trade count if needed
        self.reset_daily_trade_count()
        
        # Check number of open positions
        num_positions = self.check_open_positions()
        if num_positions >= config.MAX_POSITIONS:
            logger.info(f"Max positions reached ({num_positions}/{config.MAX_POSITIONS})")
            return False
        
        # Check daily trade limit
        if self.trades_today >= config.MAX_TRADES_PER_DAY:
            logger.info(f"Max daily trades reached ({self.trades_today}/{config.MAX_TRADES_PER_DAY})")
            return False
        
        return True
    
    def calculate_risk_amount(self, balance):
        """
        Calculate the amount to risk based on balance and config.
        
        Args:
            balance (float): Account balance
            
        Returns:
            float: Amount to risk
        """
        return balance * config.RISK_PER_TRADE
    
    def open_long_position(self, current_price, atr_value):
        """
        Open a long position with stop loss and take profit.
        
        Args:
            current_price (float): Current market price
            atr_value (float): Current ATR value
            
        Returns:
            dict: Order information
        """
        try:
            # Get account balance
            balance = self.exchange.get_balance()
            usdt_balance = balance['total']['USDT']
            
            # Calculate risk amount
            risk_amount = self.calculate_risk_amount(usdt_balance)
            
            # Calculate stop loss and take profit levels
            stop_loss = current_price - (atr_value * config.STOP_LOSS_ATR_MULTIPLIER)
            take_profit1 = current_price + (atr_value * config.TAKE_PROFIT1_ATR_MULTIPLIER)
            take_profit2 = current_price + (atr_value * config.TAKE_PROFIT2_ATR_MULTIPLIER)
            
            # Calculate position size
            position_size = self.exchange.calculate_position_size(current_price, risk_amount, stop_loss)
            
            # Set leverage
            self.exchange.set_leverage(config.LEVERAGE)
            
            # Place market order
            market_order = self.exchange.create_market_order('buy', position_size)
            
            # Place stop loss order
            stop_loss_order = self.exchange.create_stop_loss_order('sell', position_size, stop_loss)
            
            # Place take profit orders - 50% at each level
            take_profit_size1 = position_size * 0.5
            take_profit_size2 = position_size * 0.5
            take_profit_order1 = self.exchange.create_take_profit_order('sell', take_profit_size1, take_profit1)
            take_profit_order2 = self.exchange.create_take_profit_order('sell', take_profit_size2, take_profit2)
            
            # Increment trade counter
            self.trades_today += 1
            
            # Log the trade
            trade_info = {
                'type': 'LONG',
                'entry_time': datetime.now(),
                'entry_price': current_price,
                'position_size': position_size,
                'stop_loss': stop_loss,
                'take_profit1': take_profit1,
                'take_profit2': take_profit2,
                'market_order_id': market_order['id'],
                'stop_loss_order_id': stop_loss_order['id'],
                'take_profit_order1_id': take_profit_order1['id'],
                'take_profit_order2_id': take_profit_order2['id']
            }
            self.trade_log.append(trade_info)
            
            # Send notification
            self.notifier.send_trade_notification(
                'LONG', self.symbol, current_price, position_size, 
                stop_loss, f"TP1: {take_profit1}, TP2: {take_profit2}"
            )
            
            logger.info(f"Opened LONG position: {position_size} {self.symbol} at {current_price}")
            return market_order
        
        except Exception as e:
            error_msg = f"Failed to open long position: {e}"
            logger.error(error_msg)
            self.notifier.send_error_notification(error_msg)
            return None
    
    def open_short_position(self, current_price, atr_value):
        """
        Open a short position with stop loss and take profit.
        
        Args:
            current_price (float): Current market price
            atr_value (float): Current ATR value
            
        Returns:
            dict: Order information
        """
        try:
            # Get account balance
            balance = self.exchange.get_balance()
            usdt_balance = balance['total']['USDT']
            
            # Calculate risk amount
            risk_amount = self.calculate_risk_amount(usdt_balance)
            
            # Calculate stop loss and take profit levels
            stop_loss = current_price + (atr_value * config.STOP_LOSS_ATR_MULTIPLIER)
            take_profit1 = current_price - (atr_value * config.TAKE_PROFIT1_ATR_MULTIPLIER)
            take_profit2 = current_price - (atr_value * config.TAKE_PROFIT2_ATR_MULTIPLIER)
            
            # Calculate position size
            position_size = self.exchange.calculate_position_size(current_price, risk_amount, stop_loss)
            
            # Set leverage
            self.exchange.set_leverage(config.LEVERAGE)
            
            # Place market order
            market_order = self.exchange.create_market_order('sell', position_size)
            
            # Place stop loss order
            stop_loss_order = self.exchange.create_stop_loss_order('buy', position_size, stop_loss)
            
            # Place take profit orders - 50% at each level
            take_profit_size1 = position_size * 0.5
            take_profit_size2 = position_size * 0.5
            take_profit_order1 = self.exchange.create_take_profit_order('buy', take_profit_size1, take_profit1)
            take_profit_order2 = self.exchange.create_take_profit_order('buy', take_profit_size2, take_profit2)
            
            # Increment trade counter
            self.trades_today += 1
            
            # Log the trade
            trade_info = {
                'type': 'SHORT',
                'entry_time': datetime.now(),
                'entry_price': current_price,
                'position_size': position_size,
                'stop_loss': stop_loss,
                'take_profit1': take_profit1,
                'take_profit2': take_profit2,
                'market_order_id': market_order['id'],
                'stop_loss_order_id': stop_loss_order['id'],
                'take_profit_order1_id': take_profit_order1['id'],
                'take_profit_order2_id': take_profit_order2['id']
            }
            self.trade_log.append(trade_info)
            
            # Send notification
            self.notifier.send_trade_notification(
                'SHORT', self.symbol, current_price, position_size, 
                stop_loss, f"TP1: {take_profit1}, TP2: {take_profit2}"
            )
            
            logger.info(f"Opened SHORT position: {position_size} {self.symbol} at {current_price}")
            return market_order
        
        except Exception as e:
            error_msg = f"Failed to open short position: {e}"
            logger.error(error_msg)
            self.notifier.send_error_notification(error_msg)
            return None
    
    def close_position(self, position_type):
        """
        Close an open position.
        
        Args:
            position_type (str): 'long' or 'short'
            
        Returns:
            dict: Order information
        """
        try:
            # Get open positions
            positions = self.exchange.get_open_positions()
            
            # Find the position to close
            position_to_close = None
            for position in positions:
                if position_type == 'long' and position['info']['side'] == 'buy':
                    position_to_close = position
                    break
                elif position_type == 'short' and position['info']['side'] == 'sell':
                    position_to_close = position
                    break
            
            if not position_to_close:
                logger.warning(f"No {position_type} position found to close")
                return None
            
            # Cancel existing orders for this symbol
            self.exchange.cancel_all_orders()
            
            # Close position
            position_size = abs(float(position_to_close['info']['size']))
            if position_type == 'long':
                order = self.exchange.create_market_order('sell', position_size)
                trade_type = 'CLOSE LONG'
            else:
                order = self.exchange.create_market_order('buy', position_size)
                trade_type = 'CLOSE SHORT'
            
            # Get current price
            current_price = float(position_to_close['info']['markPrice'])
            
            # Send notification
            self.notifier.send_trade_notification(
                trade_type, self.symbol, current_price, position_size
            )
            
            logger.info(f"Closed {position_type} position: {position_size} {self.symbol} at {current_price}")
            return order
        
        except Exception as e:
            error_msg = f"Failed to close {position_type} position: {e}"
            logger.error(error_msg)
            self.notifier.send_error_notification(error_msg)
            return None
    
    def run_once(self):
        """
        Run one iteration of the trading strategy.
        """
        try:
            # Get market data with indicators
            df = self.get_market_data(limit=100)
            
            # Get the most recent candles
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Check for crossover events in the latest candles
            ema_crossover_recent = any(df['ema_crossover'].iloc[-3:] == 1)
            macd_crossover_recent = any(df['macd_crossover'].iloc[-3:] == 1)
            
            # Get signal and current price
            signal = latest['signal']
            current_price = latest['close']
            atr_value = latest['atr']
            
            # Check open positions
            num_positions = self.check_open_positions()
            
            # Log current state and indicators
            logger.info(f"Current price: {current_price}, Signal: {signal}, ATR: {atr_value}")
            logger.info(f"EMA crossover recent: {ema_crossover_recent}, MACD crossover recent: {macd_crossover_recent}")
            logger.info(f"EMA fast: {latest['ema_9']:.2f}, EMA slow: {latest['ema_21']:.2f}")
            logger.info(f"MACD: {latest['macd']:.4f}, MACD Signal: {latest['macd_signal']:.4f}, MACD Diff: {latest['macd_diff']:.4f}")
            logger.info(f"Open positions: {num_positions}/{config.MAX_POSITIONS}, Trades today: {self.trades_today}/{config.MAX_TRADES_PER_DAY}")
            
            # Process signals
            if signal == 1:  # Long signal
                if self.can_open_new_trade():
                    logger.info("Opening LONG position based on EMA + MACD bullish crossover")
                    self.open_long_position(current_price, atr_value)
                else:
                    logger.warning("LONG signal detected but cannot open new trade. Check max positions or daily trade limit.")
            
            # Özel durum: EMA ve MACD yakın zamanda bullish sinyal vermişse ancak henüz signal==1 olmamışsa
            elif ema_crossover_recent and macd_crossover_recent and not signal == 1:
                logger.info("Detected recent EMA and MACD bullish crossovers, but no confirmed signal yet.")
                if self.can_open_new_trade():
                    logger.info("Opening LONG position based on recent EMA + MACD bullish crossovers")
                    self.open_long_position(current_price, atr_value)
                else:
                    logger.warning("Recent bullish crossovers detected but cannot open new trade. Check max positions or daily trade limit.")
            
            elif signal == -1:  # Short signal
                if self.can_open_new_trade():
                    logger.info("Opening SHORT position based on EMA + MACD bearish crossover")
                    self.open_short_position(current_price, atr_value)
                else:
                    logger.warning("SHORT signal detected but cannot open new trade. Check max positions or daily trade limit.")
            
            # Check for exit conditions
            for position in self.open_positions:
                position_side = position['info']['side']
                
                # Exit long position
                if position_side == 'buy' and latest['ema_crossover'] == -1 and latest['macd_crossover'] == -1:
                    logger.info("Closing LONG position based on EMA + MACD bearish crossover")
                    self.close_position('long')
                
                # Exit short position
                elif position_side == 'sell' and latest['ema_crossover'] == 1 and latest['macd_crossover'] == 1:
                    logger.info("Closing SHORT position based on EMA + MACD bullish crossover")
                    self.close_position('short')
        
        except Exception as e:
            error_msg = f"Error in trading iteration: {e}"
            logger.error(error_msg, exc_info=True)  # exc_info=True ekleyerek stack trace gösterilmesini sağlıyoruz
            self.notifier.send_error_notification(error_msg)
    
    def run(self, interval=60):
        """
        Run the trading bot continuously.
        
        Args:
            interval (int): Sleep interval between iterations in seconds
        """
        logger.info(f"Starting trading bot for {self.symbol} on {self.timeframe} timeframe")
        
        try:
            while True:
                self.run_once()
                logger.info(f"Sleeping for {interval} seconds")
                time.sleep(interval)
        
        except KeyboardInterrupt:
            logger.info("Trading bot stopped by user")
        except Exception as e:
            error_msg = f"Trading bot stopped due to error: {e}"
            logger.error(error_msg)
            self.notifier.send_error_notification(error_msg) 