"""
Exchange connection module for interacting with Bitget API.
Handles market data retrieval and order execution.
"""
import ccxt
import pandas as pd
import time
from datetime import datetime
import logging
from retry import retry

from src import config

# Configure logging
logger = logging.getLogger(__name__)

class BitgetExchange:
    """
    Wrapper class for interacting with Bitget exchange via CCXT.
    """
    
    def __init__(self):
        """Initialize the Bitget exchange connection."""
        self.exchange = self._initialize_exchange()
        self.symbol = config.SYMBOL
        self.timeframe = config.TIMEFRAME
        
    def _initialize_exchange(self):
        """
        Initialize the CCXT Bitget exchange object.
        
        Returns:
            ccxt.bitget: Initialized exchange object
        """
        try:
            exchange = ccxt.bitget({
                'apiKey': config.API_KEY,
                'secret': config.API_SECRET,
                'password': config.API_PASSPHRASE,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'swap',
                }
            })
            return exchange
        except Exception as e:
            logger.error(f"Failed to initialize Bitget exchange: {e}")
            raise
    
    @retry(tries=3, delay=2, backoff=2)
    def get_balance(self):
        """
        Get account balance.
        
        Returns:
            dict: Account balance information
        """
        try:
            balance = self.exchange.fetch_balance()
            return balance
        except Exception as e:
            logger.error(f"Failed to fetch balance: {e}")
            raise
    
    @retry(tries=3, delay=2, backoff=2)
    def fetch_ohlcv(self, limit=100):
        """
        Fetch OHLCV data from the exchange.
        
        Args:
            limit (int): Number of candles to fetch
            
        Returns:
            pandas.DataFrame: OHLCV data
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(
                symbol=self.symbol,
                timeframe=self.timeframe,
                limit=limit
            )
            
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV data: {e}")
            raise
    
    @retry(tries=3, delay=2, backoff=2)
    def set_leverage(self, leverage=config.LEVERAGE):
        """
        Set leverage for trading.
        
        Args:
            leverage (int): Leverage value
            
        Returns:
            dict: Response from the exchange
        """
        try:
            response = self.exchange.set_leverage(leverage, self.symbol)
            logger.info(f"Leverage set to {leverage} for {self.symbol}")
            return response
        except Exception as e:
            logger.error(f"Failed to set leverage: {e}")
            raise
    
    def calculate_position_size(self, price, risk_amount, stop_loss_price):
        """
        Calculate position size based on risk parameters.
        
        Args:
            price (float): Current market price
            risk_amount (float): Amount willing to risk
            stop_loss_price (float): Stop loss price
            
        Returns:
            float: Position size in contract units
        """
        if price == stop_loss_price:
            logger.warning("Price and stop loss are the same, cannot calculate position size")
            return 0
            
        risk_per_contract = abs(price - stop_loss_price)
        position_size = risk_amount / risk_per_contract
        
        return position_size
    
    @retry(tries=3, delay=2, backoff=2)
    def create_market_order(self, side, amount):
        """
        Create a market order.
        
        Args:
            side (str): 'buy' or 'sell'
            amount (float): Amount to buy/sell
            
        Returns:
            dict: Order information
        """
        try:
            order = self.exchange.create_order(
                symbol=self.symbol,
                type='market',
                side=side,
                amount=amount
            )
            logger.info(f"Created {side} market order for {amount} {self.symbol}")
            return order
        except Exception as e:
            logger.error(f"Failed to create market order: {e}")
            raise
    
    @retry(tries=3, delay=2, backoff=2)
    def create_limit_order(self, side, amount, price):
        """
        Create a limit order.
        
        Args:
            side (str): 'buy' or 'sell'
            amount (float): Amount to buy/sell
            price (float): Limit price
            
        Returns:
            dict: Order information
        """
        try:
            order = self.exchange.create_order(
                symbol=self.symbol,
                type='limit',
                side=side,
                amount=amount,
                price=price
            )
            logger.info(f"Created {side} limit order for {amount} {self.symbol} at {price}")
            return order
        except Exception as e:
            logger.error(f"Failed to create limit order: {e}")
            raise
    
    @retry(tries=3, delay=2, backoff=2)
    def create_stop_loss_order(self, side, amount, stop_price, price=None):
        """
        Create a stop loss order.
        
        Args:
            side (str): 'buy' or 'sell'
            amount (float): Amount to buy/sell
            stop_price (float): Trigger price
            price (float, optional): Limit price (if None, will be a stop market)
            
        Returns:
            dict: Order information
        """
        try:
            order_type = 'stop_market' if price is None else 'stop_limit'
            params = {'stopPrice': stop_price}
            
            if price is not None:
                params['price'] = price
            
            order = self.exchange.create_order(
                symbol=self.symbol,
                type=order_type,
                side=side,
                amount=amount,
                params=params
            )
            logger.info(f"Created {side} stop loss order for {amount} {self.symbol} at trigger {stop_price}")
            return order
        except Exception as e:
            logger.error(f"Failed to create stop loss order: {e}")
            raise
    
    @retry(tries=3, delay=2, backoff=2)
    def create_take_profit_order(self, side, amount, take_profit_price, price=None):
        """
        Create a take profit order.
        
        Args:
            side (str): 'buy' or 'sell'
            amount (float): Amount to buy/sell
            take_profit_price (float): Trigger price
            price (float, optional): Limit price (if None, will be a take profit market)
            
        Returns:
            dict: Order information
        """
        try:
            order_type = 'take_profit_market' if price is None else 'take_profit_limit'
            params = {'triggerPrice': take_profit_price}
            
            if price is not None:
                params['price'] = price
            
            order = self.exchange.create_order(
                symbol=self.symbol,
                type=order_type,
                side=side,
                amount=amount,
                params=params
            )
            logger.info(f"Created {side} take profit order for {amount} {self.symbol} at trigger {take_profit_price}")
            return order
        except Exception as e:
            logger.error(f"Failed to create take profit order: {e}")
            raise
    
    @retry(tries=3, delay=2, backoff=2)
    def cancel_all_orders(self):
        """
        Cancel all open orders for the symbol.
        
        Returns:
            list: Cancelled orders
        """
        try:
            cancelled = self.exchange.cancel_all_orders(self.symbol)
            logger.info(f"Cancelled all orders for {self.symbol}")
            return cancelled
        except Exception as e:
            logger.error(f"Failed to cancel orders: {e}")
            raise
    
    @retry(tries=3, delay=2, backoff=2)
    def get_open_positions(self):
        """
        Get all open positions.
        
        Returns:
            list: Open positions
        """
        try:
            positions = self.exchange.fetch_positions([self.symbol])
            return positions
        except Exception as e:
            logger.error(f"Failed to fetch positions: {e}")
            raise
    
    @retry(tries=3, delay=2, backoff=2)
    def get_open_orders(self):
        """
        Get all open orders.
        
        Returns:
            list: Open orders
        """
        try:
            orders = self.exchange.fetch_open_orders(self.symbol)
            return orders
        except Exception as e:
            logger.error(f"Failed to fetch open orders: {e}")
            raise 