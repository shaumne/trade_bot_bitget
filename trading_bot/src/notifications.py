"""
Notification module for sending email alerts about trades.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from src import config

# Configure logging
logger = logging.getLogger(__name__)

class EmailNotifier:
    """
    Class for sending email notifications.
    """
    
    def __init__(self):
        """Initialize the email notifier with configuration."""
        self.sender_email = config.EMAIL_SENDER
        self.recipient_email = config.EMAIL_RECIPIENT
        self.password = config.EMAIL_PASSWORD
        self.smtp_server = config.SMTP_SERVER
        self.smtp_port = config.SMTP_PORT
    
    def send_email(self, subject, message):
        """
        Send an email notification.
        
        Args:
            subject (str): Email subject
            message (str): Email body content
            
        Returns:
            bool: Success status
        """
        if not all([self.sender_email, self.recipient_email, self.password, self.smtp_server]):
            logger.warning("Email configuration incomplete, notification not sent")
            return False
        
        try:
            # Create a multipart message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = subject
            
            # Add message body
            msg.attach(MIMEText(message, 'plain'))
            
            # Connect to SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.password)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email notification sent to {self.recipient_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False
    
    def send_trade_notification(self, trade_type, symbol, entry_price, position_size, stop_loss=None, take_profit=None):
        """
        Send a trade notification.
        
        Args:
            trade_type (str): Type of trade ('LONG', 'SHORT', 'CLOSE LONG', 'CLOSE SHORT')
            symbol (str): Trading symbol
            entry_price (float): Entry price
            position_size (float): Position size
            stop_loss (float, optional): Stop loss price
            take_profit (float, optional): Take profit price
            
        Returns:
            bool: Success status
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subject = f"Trade Alert: {trade_type} {symbol} at {timestamp}"
        
        message = f"""
Trade Details:
--------------
Type: {trade_type}
Symbol: {symbol}
Time: {timestamp}
Entry Price: {entry_price}
Position Size: {position_size}
"""
        
        if stop_loss:
            message += f"Stop Loss: {stop_loss}\n"
        
        if take_profit:
            message += f"Take Profit: {take_profit}\n"
        
        message += "\nThis is an automated message from your trading bot."
        
        return self.send_email(subject, message)
    
    def send_error_notification(self, error_message):
        """
        Send an error notification.
        
        Args:
            error_message (str): Error message
            
        Returns:
            bool: Success status
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subject = f"Trading Bot Error at {timestamp}"
        
        message = f"""
Error in Trading Bot:
--------------------
Time: {timestamp}
Error: {error_message}

Please check your trading bot.
"""
        
        return self.send_email(subject, message) 