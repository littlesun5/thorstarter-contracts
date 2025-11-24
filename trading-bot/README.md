# BTC RSI Trading Bot for Backpack Exchange

An automated trading bot that uses RSI (Relative Strength Index) indicators to trade BTC on Backpack Exchange with advanced position management and risk control features.

## 🚨 WARNING

**This bot trades with REAL MONEY. Use at your own risk!**
- Always test thoroughly on testnet first
- Start with small amounts
- Monitor closely during operation
- Never invest more than you can afford to lose
- Past performance does not guarantee future results

## 📋 Features

### Trading Strategy
- **RSI-based signals**: Opens positions when RSI crosses oversold (<29) or overbought (>71) levels
- **Automatic position management**: Closes positions when profit covers fees
- **Dynamic scaling**: Adds to positions at predefined price levels
- **Risk management**: Automatic stop-loss at $1000 loss

### Position Scaling (Dollar-Cost Averaging)
When a position moves against you, the bot automatically scales in:
- $150 drawdown: Add 0.05 BTC
- $250 drawdown: Add 0.08 BTC
- $500 drawdown: Add 0.1 BTC
- $800 drawdown: Add 0.15 BTC
- $1200 drawdown: Add 0.2 BTC
- $1500 drawdown: Add 0.3 BTC

### Safety Features
- Maximum position size: 2 BTC
- Minimum 20-second interval between orders
- Automatic stop-loss at $1000 loss
- Market order fee consideration (0.02%)
- Limit order support for 0% fees

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- Backpack Exchange account with API access
- API key and secret from Backpack Exchange

### Quick Setup

1. **Clone or download the trading bot**
```bash
cd trading-bot
```

2. **Run the setup script**
```bash
python setup.py
```

3. **Configure your API credentials**
Edit the `.env` file and add your Backpack Exchange API credentials:
```env
BACKPACK_API_KEY=your_actual_api_key_here
BACKPACK_API_SECRET=your_actual_api_secret_here
```

4. **Test the connection**
```bash
python src/test_connection.py
```

5. **Start the bot**
```bash
python src/trading_bot.py
```

## ⚙️ Configuration

All configuration is done through the `.env` file:

### API Configuration
```env
BACKPACK_API_KEY=your_api_key
BACKPACK_API_SECRET=your_api_secret
USE_TESTNET=true  # Set to false for mainnet
```

### Trading Parameters
```env
SYMBOL=BTC-USDT
RSI_PERIOD=14
RSI_OVERSOLD=29
RSI_OVERBOUGHT=71
```

### Position Management
```env
INITIAL_POSITION_SIZE=0.03
SCALE_IN_SIZES=0.05,0.08,0.1,0.15,0.2,0.3
SCALE_IN_THRESHOLDS=150,250,500,800,1200,1500
MAX_POSITION_SIZE=2.0
```

### Risk Management
```env
STOP_LOSS_USD=1000
MIN_ORDER_INTERVAL=20
```

### Fees
```env
MARKET_FEE=0.0002  # 0.02%
LIMIT_FEE=0.0      # 0%
```

### Monitoring
```env
CHECK_INTERVAL=60  # Check every 60 seconds
DATA_SOURCE=binance  # or 'backpack'
```

## 🚀 Usage

### Starting the Bot
```bash
# Run in production mode
python src/trading_bot.py

# Run in testnet mode (recommended for testing)
# Set USE_TESTNET=true in .env file
```

### Monitoring
Open a separate terminal to monitor the bot:
```bash
python src/monitor.py
```

### Stopping the Bot
Press `Ctrl+C` to safely stop the bot. It will:
- Complete any pending operations
- Display a summary of open positions
- Show recent trade history

## 📊 How It Works

1. **Data Collection**: Fetches price data from Binance or Backpack every minute
2. **RSI Calculation**: Calculates 14-period RSI from closing prices
3. **Signal Generation**: 
   - RSI > 71: Open SHORT position
   - RSI < 29: Open LONG position
4. **Position Management**:
   - Monitor unrealized P&L
   - Scale into positions at predefined levels
   - Close when profit covers fees
   - Emergency stop-loss at $1000 loss

## 🔧 Advanced Usage

### Using Different Data Sources
The bot can use either Binance or Backpack for price data:
```env
DATA_SOURCE=binance  # More liquid, recommended
DATA_SOURCE=backpack  # Use Backpack's own data
```

### Adjusting RSI Parameters
Modify RSI sensitivity:
```env
RSI_PERIOD=21  # Longer period for smoother signals
RSI_OVERSOLD=25  # More conservative long entry
RSI_OVERBOUGHT=75  # More conservative short entry
```

### Custom Position Sizing
Adjust position sizes and thresholds:
```env
INITIAL_POSITION_SIZE=0.01  # Start smaller
MAX_POSITION_SIZE=1.0  # Reduce maximum exposure
```

## 📁 Project Structure

```
trading-bot/
├── src/
│   ├── backpack_api.py      # Backpack Exchange API client
│   ├── rsi_calculator.py    # RSI calculation module
│   ├── position_manager.py  # Position and risk management
│   ├── trading_bot.py       # Main bot logic
│   ├── monitor.py           # Monitoring dashboard
│   └── test_connection.py   # Connection tester
├── logs/                    # Trading logs (created automatically)
├── .env                     # Configuration (create from .env.example)
├── .env.example            # Configuration template
├── requirements.txt        # Python dependencies
├── setup.py               # Setup script
└── README.md             # This file
```

## 🐛 Troubleshooting

### Connection Issues
- Verify API credentials in `.env` file
- Check if using correct network (testnet vs mainnet)
- Ensure API has trading permissions enabled

### No RSI Signals
- Insufficient price history (needs 15+ data points)
- Check DATA_SOURCE setting
- Verify symbol format (BTC-USDT for Backpack, BTCUSDT for Binance)

### Orders Not Executing
- Check account balance
- Verify API trading permissions
- Review order size limits on exchange
- Check MIN_ORDER_INTERVAL setting

## 🔒 Security Best Practices

1. **API Key Security**
   - Never share your API keys
   - Use IP whitelist on Backpack
   - Enable withdrawal whitelist
   - Disable withdrawal permissions for trading API

2. **Risk Management**
   - Start with testnet
   - Use small position sizes initially
   - Set appropriate stop-loss levels
   - Monitor actively during first runs

3. **System Security**
   - Keep `.env` file private
   - Don't commit `.env` to version control
   - Run on secure, dedicated server
   - Use firewall to restrict access

## 📈 Performance Tips

1. **Optimize RSI Settings**
   - Test different RSI periods (9, 14, 21)
   - Adjust oversold/overbought levels based on market conditions

2. **Position Management**
   - Start with smaller positions
   - Adjust scaling thresholds based on volatility
   - Use limit orders when possible for 0% fees

3. **Monitoring**
   - Keep logs for analysis
   - Track win/loss ratios
   - Adjust strategy based on performance

## ⚠️ Disclaimer

This software is provided "as is", without warranty of any kind. The authors are not responsible for any losses incurred through the use of this software. Cryptocurrency trading carries significant risk. Only trade with funds you can afford to lose.

## 📞 Support

For issues related to:
- **Backpack Exchange API**: Consult [Backpack Documentation](https://docs.backpack.exchange/)
- **Bot Issues**: Check logs in `logs/` directory
- **Configuration**: Review `.env.example` for all options

## 📝 License

This project is for educational purposes. Use at your own risk.

---

**Remember**: Always test on testnet first! Set `USE_TESTNET=true` in your `.env` file.