"""
Trading Bot Monitor
Real-time monitoring dashboard for the trading bot
"""

import os
import sys
import time
from datetime import datetime
from typing import Dict, List
import requests
import logging
from dotenv import load_dotenv
import colorlog

# Configure logging
handler = colorlog.StreamHandler()
handler.setFormatter(
    colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S',
        log_colors={
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
        }
    )
)

logger = colorlog.getLogger('Monitor')
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class TradingMonitor:
    def __init__(self):
        """Initialize the trading monitor"""
        load_dotenv('.env')
        self.symbol = os.getenv('SYMBOL', 'BTC-USDT')
        self.rsi_oversold = float(os.getenv('RSI_OVERSOLD', 29))
        self.rsi_overbought = float(os.getenv('RSI_OVERBOUGHT', 71))
        
    def get_binance_price(self) -> float:
        """Get current BTC price from Binance"""
        try:
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT')
            data = response.json()
            return float(data['price'])
        except:
            return 0
    
    def get_binance_24h_stats(self) -> Dict:
        """Get 24h statistics from Binance"""
        try:
            response = requests.get('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT')
            data = response.json()
            return {
                'high': float(data['highPrice']),
                'low': float(data['lowPrice']),
                'volume': float(data['volume']),
                'change': float(data['priceChangePercent'])
            }
        except:
            return {'high': 0, 'low': 0, 'volume': 0, 'change': 0}
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_dashboard(self):
        """Display the monitoring dashboard"""
        self.clear_screen()
        
        # Get current data
        price = self.get_binance_price()
        stats = self.get_binance_24h_stats()
        
        # Display header
        print("=" * 60)
        print(f"{'TRADING BOT MONITOR':^60}")
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S'):^60}")
        print("=" * 60)
        
        # Market Data
        print("\n📊 MARKET DATA")
        print("-" * 40)
        print(f"Symbol:          {self.symbol}")
        print(f"Current Price:   ${price:,.2f}")
        print(f"24h High:        ${stats['high']:,.2f}")
        print(f"24h Low:         ${stats['low']:,.2f}")
        print(f"24h Change:      {stats['change']:+.2f}%")
        print(f"24h Volume:      {stats['volume']:,.2f} BTC")
        
        # RSI Settings
        print("\n📈 RSI CONFIGURATION")
        print("-" * 40)
        print(f"Oversold Level:  < {self.rsi_oversold}")
        print(f"Overbought Level: > {self.rsi_overbought}")
        
        # Position Management
        print("\n💼 POSITION MANAGEMENT")
        print("-" * 40)
        print(f"Initial Size:    {os.getenv('INITIAL_POSITION_SIZE', '0.03')} BTC")
        print(f"Max Position:    {os.getenv('MAX_POSITION_SIZE', '2.0')} BTC")
        print(f"Stop Loss:       ${os.getenv('STOP_LOSS_USD', '1000')}")
        
        # Scale-in Levels
        print("\n📊 SCALE-IN LEVELS")
        print("-" * 40)
        sizes = os.getenv('SCALE_IN_SIZES', '0.05,0.08,0.1,0.15,0.2,0.3').split(',')
        thresholds = os.getenv('SCALE_IN_THRESHOLDS', '150,250,500,800,1200,1500').split(',')
        
        for i, (threshold, size) in enumerate(zip(thresholds, sizes), 1):
            print(f"Level {i}: ${threshold:>4} -> {size} BTC")
        
        # Instructions
        print("\n" + "=" * 60)
        print("Press Ctrl+C to exit")
        print("=" * 60)
    
    def run(self):
        """Run the monitor"""
        try:
            while True:
                self.display_dashboard()
                time.sleep(5)  # Update every 5 seconds
        except KeyboardInterrupt:
            print("\nMonitor stopped.")
            sys.exit(0)


if __name__ == "__main__":
    monitor = TradingMonitor()
    monitor.run()