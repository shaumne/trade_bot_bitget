# Bitget Trading Bot

A trading bot for Bitget cryptocurrency exchange that implements an EMA + MACD crossover strategy.

## Strategy

The trading bot follows these rules:

1. **Entry Conditions**
   - **LONG**: When EMA(9,21) makes a bullish crossover AND MACD(12,26,9) makes a bullish crossover
   - **SHORT**: When EMA(9,21) makes a bearish crossover AND MACD(12,26,9) makes a bearish crossover

2. **Exit Conditions**
   - **Close LONG**: When EMA and MACD make bearish crossovers
   - **Close SHORT**: When EMA and MACD make bullish crossovers

3. **Risk Management**
   - **Stop Loss**: 2× ATR
   - **Take Profit 1**: 3× ATR (50% of position)
   - **Take Profit 2**: 5× ATR (50% of position)

4. **Trade Rules**
   - Risk per trade: 50% of wallet balance
   - Maximum number of open positions: 2
   - Maximum number of trades per day: 6
   - Email notifications on order execution

## Setup

### Requirements

- Python 3.8+
- Bitget API credentials

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd trading_bot
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory and set your configuration:
   ```
   cp .env.example .env
   # Edit .env file with your credentials and preferences
   ```

### Configuration

Edit the `.env` file to configure the trading bot:

```
# Bitget API Credentials
BITGET_API_KEY=your_api_key_here
BITGET_API_SECRET=your_api_secret_here
BITGET_API_PASSPHRASE=your_passphrase_here

# Trading Parameters
SYMBOL=BTCUSDT
LEVERAGE=1
TIMEFRAME=15m

# Risk Management
RISK_PER_TRADE=0.5  # 50% of wallet balance
MAX_POSITIONS=2
MAX_TRADES_PER_DAY=6

# Email Notifications
EMAIL_RECIPIENT=your_email@example.com
EMAIL_SENDER=bot_email@example.com
EMAIL_PASSWORD=your_email_password
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
```

## Usage

### Running the Trading Bot

To start the trading bot:

```
python main.py trade
```

Options:
- `--interval`: Interval between trading iterations in seconds (default: 60)

### Running Backtests

To run a backtest of the strategy:

```
python main.py backtest --start-date 2023-03-01 --end-date 2023-04-01
```

Backtest results will be saved in the `backtest_results` directory.

## Project Structure

```
trading_bot/
├── config/           # Configuration files
├── logs/             # Log files
├── src/              # Source code
│   ├── backtest.py   # Backtesting module
│   ├── config.py     # Configuration handling
│   ├── exchange.py   # Exchange connectivity
│   ├── indicators.py # Technical indicators
│   ├── notifications.py # Email notifications
│   └── trader.py     # Main trading logic
├── tests/            # Test modules
├── .env.example      # Example environment variables
├── main.py           # Main entry point
├── README.md         # This file
└── requirements.txt  # Dependencies
```

## AWS Deployment

To deploy the trading bot to AWS:

1. Launch an EC2 instance
2. Clone the repository to the instance
3. Install dependencies
4. Create the `.env` file with proper configuration
5. Set up a systemd service or use screen/tmux to run the bot in the background

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This trading bot is for educational purposes only. Use at your own risk. Cryptocurrency trading involves significant risk and you can lose your funds. Always test thoroughly before using with real funds. 