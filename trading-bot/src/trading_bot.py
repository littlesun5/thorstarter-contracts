"""
Main Trading Bot
Implements RSI-based trading strategy with position management
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv
import colorlog

from backpack_api import BackpackAPI
from rsi_calculator import RSICalculator
from position_manager import PositionManager

# Configure colored logging
handler = colorlog.StreamHandler()
handler.setFormatter(
    colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
)

logger = colorlog.getLogger('TradingBot')
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class TradingBot:
    def __init__(self, config_path: str = '.env'):
        """
        Initialize Trading Bot
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        load_dotenv(config_path)
        self.config = self._load_config()
        
        # Initialize components
        self.api = BackpackAPI(
            api_key=self.config['BACKPACK_API_KEY'],
            api_secret=self.config['BACKPACK_API_SECRET'],
            testnet=self.config.get('USE_TESTNET', False)
        )
        
        self.rsi_calculator = RSICalculator(period=int(self.config.get('RSI_PERIOD', 14)))
        self.position_manager = PositionManager(self.config)
        
        # Trading parameters
        self.symbol = self.config.get('SYMBOL', 'BTC-USDT')
        self.rsi_oversold = float(self.config.get('RSI_OVERSOLD', 29))
        self.rsi_overbought = float(self.config.get('RSI_OVERBOUGHT', 71))
        self.check_interval = int(self.config.get('CHECK_INTERVAL', 60))
        
        # State tracking
        self.last_rsi = None
        self.last_price = None
        self.running = False
        
        logger.info(f"Trading Bot initialized for {self.symbol}")
        logger.info(f"RSI thresholds: Oversold={self.rsi_oversold}, Overbought={self.rsi_overbought}")
    
    def _load_config(self) -> Dict:
        """Load configuration from environment variables"""
        config = {}
        
        # Required configurations
        required_keys = ['BACKPACK_API_KEY', 'BACKPACK_API_SECRET']
        for key in required_keys:
            value = os.getenv(key)
            if not value:
                raise ValueError(f"Missing required configuration: {key}")
            config[key] = value
        
        # Optional configurations with defaults
        optional_configs = {
            'USE_TESTNET': 'false',
            'SYMBOL': 'BTC-USDT',
            'RSI_PERIOD': '14',
            'RSI_OVERSOLD': '29',
            'RSI_OVERBOUGHT': '71',
            'INITIAL_POSITION_SIZE': '0.03',
            'SCALE_IN_SIZES': '0.05,0.08,0.1,0.15,0.2,0.3',
            'SCALE_IN_THRESHOLDS': '150,250,500,800,1200,1500',
            'MAX_POSITION_SIZE': '2.0',
            'STOP_LOSS_USD': '1000',
            'MIN_ORDER_INTERVAL': '20',
            'MARKET_FEE': '0.0002',
            'LIMIT_FEE': '0',
            'CHECK_INTERVAL': '60',
            'DATA_SOURCE': 'binance'  # 'binance' or 'backpack'
        }
        
        for key, default in optional_configs.items():
            config[key] = os.getenv(key, default)
        
        # Convert boolean string
        config['USE_TESTNET'] = config['USE_TESTNET'].lower() == 'true'
        
        return config
    
    def get_current_price(self) -> Optional[float]:
        """Get current BTC price from Backpack"""
        try:
            ticker = self.api.get_ticker(self.symbol)
            return float(ticker.get('lastPrice', 0))
        except Exception as e:
            logger.error(f"Failed to get current price: {e}")
            return None
    
    def execute_trade(self, side: str, quantity: float, order_type: str = 'market') -> bool:
        """
        Execute a trade on Backpack Exchange
        
        Args:
            side: 'buy' or 'sell'
            quantity: Order quantity
            order_type: 'market' or 'limit'
        
        Returns:
            True if successful
        """
        try:
            # For futures/perps, we need to adjust the side based on position direction
            # Long position: buy to open, sell to close
            # Short position: sell to open, buy to close
            
            order_params = {
                'symbol': self.symbol,
                'side': side,
                'order_type': order_type,
                'quantity': quantity
            }
            
            # If limit order, get best price
            if order_type == 'limit':
                orderbook = self.api.get_orderbook(self.symbol, depth=1)
                if side == 'buy':
                    # Use best ask for buy orders
                    order_params['price'] = float(orderbook['asks'][0][0])
                else:
                    # Use best bid for sell orders
                    order_params['price'] = float(orderbook['bids'][0][0])
                
                order_params['post_only'] = True  # Ensure we get maker fees
            
            result = self.api.place_order(**order_params)
            
            if result and 'orderId' in result:
                logger.info(f"Order placed successfully: {result['orderId']}")
                return True
            else:
                logger.error(f"Order failed: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to execute trade: {e}")
            return False
    
    def handle_rsi_signal(self, rsi: float, current_price: float):
        """
        Handle RSI signals and execute trades
        
        Args:
            rsi: Current RSI value
            current_price: Current BTC price
        """
        position = self.position_manager.get_position(self.symbol)
        
        # Check if we can place an order (time interval)
        if not self.position_manager.can_place_order(self.symbol):
            remaining = self.position_manager.min_order_interval - \
                       (datetime.now() - self.position_manager.last_order_time[self.symbol]).seconds
            logger.debug(f"Waiting {remaining}s before next order")
            return
        
        # If we have a position, check for scaling or closing
        if position:
            # Check if we should close the position
            should_close, close_reason = self.position_manager.should_close_position(
                self.symbol, current_price
            )
            
            if should_close:
                # Close position with market order
                close_side = 'sell' if position.side == 'long' else 'buy'
                if self.execute_trade(close_side, position.total_quantity, 'market'):
                    self.position_manager.close_position(self.symbol, current_price, close_reason)
                return
            
            # Check if we should scale into position
            should_scale, scale_size = self.position_manager.should_scale_in(
                self.symbol, current_price
            )
            
            if should_scale:
                # Scale into position
                order_side = 'buy' if position.side == 'long' else 'sell'
                if self.execute_trade(order_side, scale_size, 'limit'):
                    self.position_manager.add_to_position(self.symbol, current_price, scale_size)
                return
        
        # Check for new position signals
        if not position or position.total_quantity < self.position_manager.max_position:
            # RSI Overbought - Open Short
            if rsi > self.rsi_overbought and (not position or position.side == 'short'):
                logger.info(f"RSI Overbought signal: {rsi:.2f} > {self.rsi_overbought}")
                
                if not position:
                    # Open new short position
                    if self.execute_trade('sell', self.position_manager.initial_size, 'limit'):
                        self.position_manager.open_position(
                            self.symbol, 'short', current_price, 
                            self.position_manager.initial_size
                        )
            
            # RSI Oversold - Open Long
            elif rsi < self.rsi_oversold and (not position or position.side == 'long'):
                logger.info(f"RSI Oversold signal: {rsi:.2f} < {self.rsi_oversold}")
                
                if not position:
                    # Open new long position
                    if self.execute_trade('buy', self.position_manager.initial_size, 'limit'):
                        self.position_manager.open_position(
                            self.symbol, 'long', current_price,
                            self.position_manager.initial_size
                        )
    
    def run_cycle(self):
        """Run one trading cycle"""
        try:
            # Get current RSI and price
            data_source = self.config.get('DATA_SOURCE', 'binance')
            rsi, price = self.rsi_calculator.get_current_rsi(
                source=data_source,
                api_client=self.api if data_source == 'backpack' else None,
                symbol='BTCUSDT' if data_source == 'binance' else self.symbol
            )
            
            if rsi is None:
                logger.warning("Could not calculate RSI - insufficient data")
                return
            
            # Get actual trading price from Backpack
            current_price = self.get_current_price()
            if current_price is None:
                logger.warning("Could not get current price from Backpack")
                return
            
            # Update position PnL
            position = self.position_manager.get_position(self.symbol)
            if position:
                position.unrealized_pnl = position.calculate_pnl(current_price)
            
            # Log current status
            logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] "
                       f"RSI: {rsi:.2f} | Price: ${current_price:,.2f}")
            
            if position:
                logger.info(f"  Position: {position.side.upper()} {position.total_quantity:.3f} BTC "
                           f"| Avg Entry: ${position.average_entry_price:,.2f} "
                           f"| PnL: ${position.unrealized_pnl:,.2f}")
            
            # Store values
            self.last_rsi = rsi
            self.last_price = current_price
            
            # Handle trading signals
            self.handle_rsi_signal(rsi, current_price)
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}", exc_info=True)
    
    def start(self):
        """Start the trading bot"""
        self.running = True
        logger.info("=" * 50)
        logger.info("Trading Bot Started")
        logger.info(f"Symbol: {self.symbol}")
        logger.info(f"Check Interval: {self.check_interval} seconds")
        logger.info("=" * 50)
        
        try:
            while self.running:
                self.run_cycle()
                
                # Wait for next cycle
                logger.debug(f"Waiting {self.check_interval} seconds for next check...")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            self.stop()
        except Exception as e:
            logger.error(f"Bot crashed: {e}", exc_info=True)
            self.stop()
    
    def stop(self):
        """Stop the trading bot"""
        self.running = False
        
        # Log final summary
        summary = self.position_manager.get_position_summary()
        
        logger.info("=" * 50)
        logger.info("Trading Bot Stopped")
        logger.info(f"Open Positions: {len(summary['positions'])}")
        logger.info(f"Total Exposure: {summary['total_exposure']:.3f} BTC")
        logger.info(f"Total Unrealized PnL: ${summary['total_pnl']:,.2f}")
        
        # Log trade history
        if self.position_manager.order_history:
            logger.info("\nTrade History:")
            for trade in self.position_manager.order_history[-10:]:  # Last 10 trades
                logger.info(f"  {trade['timestamp'].strftime('%Y-%m-%d %H:%M')} - "
                           f"{trade['side'].upper()} {trade['quantity']:.3f} BTC "
                           f"PnL: ${trade['pnl']:,.2f} ({trade['reason']})")
        
        logger.info("=" * 50)


if __name__ == "__main__":
    # Check for configuration file
    config_file = '.env'
    if not os.path.exists(config_file):
        logger.error(f"Configuration file '{config_file}' not found!")
        logger.error("Please create a .env file with your API credentials.")
        logger.error("You can use .env.example as a template.")
        sys.exit(1)
    
    # Create and start bot
    bot = TradingBot(config_file)
    bot.start()