"""
RSI (Relative Strength Index) Calculator
Calculates RSI from price data using both Backpack and Binance as data sources
"""

import numpy as np
import pandas as pd
import requests
from typing import List, Optional, Tuple, Dict
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RSICalculator:
    def __init__(self, period: int = 14):
        """
        Initialize RSI Calculator
        
        Args:
            period: RSI period (default: 14)
        """
        self.period = period
        self.price_history = []
        self.rsi_history = []
        
    def calculate_rsi(self, prices: List[float]) -> Optional[float]:
        """
        Calculate RSI from price series
        
        Args:
            prices: List of prices (oldest to newest)
        
        Returns:
            Current RSI value or None if insufficient data
        """
        if len(prices) < self.period + 1:
            logger.warning(f"Insufficient data for RSI calculation. Need {self.period + 1} prices, got {len(prices)}")
            return None
        
        # Convert to numpy array
        prices = np.array(prices)
        
        # Calculate price changes
        deltas = np.diff(prices)
        
        # Separate gains and losses
        gains = deltas.copy()
        losses = deltas.copy()
        gains[gains < 0] = 0
        losses[losses > 0] = 0
        losses = abs(losses)
        
        # Calculate average gain and loss
        avg_gain = np.mean(gains[:self.period])
        avg_loss = np.mean(losses[:self.period])
        
        # Use Wilder's smoothing method for subsequent values
        for i in range(self.period, len(deltas)):
            avg_gain = (avg_gain * (self.period - 1) + gains[i]) / self.period
            avg_loss = (avg_loss * (self.period - 1) + losses[i]) / self.period
        
        # Calculate RSI
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)
    
    def get_binance_klines(self, symbol: str = 'BTCUSDT', interval: str = '1m', limit: int = 100) -> List[float]:
        """
        Fetch kline data from Binance
        
        Args:
            symbol: Trading symbol (default: BTCUSDT)
            interval: Kline interval (default: 1m)
            limit: Number of klines to fetch
        
        Returns:
            List of closing prices
        """
        try:
            url = f"https://api.binance.com/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            klines = response.json()
            # Extract closing prices (index 4 in kline data)
            closing_prices = [float(kline[4]) for kline in klines]
            
            return closing_prices
            
        except Exception as e:
            logger.error(f"Failed to fetch Binance klines: {e}")
            return []
    
    def get_backpack_klines(self, api_client, symbol: str = 'BTC-USDT', interval: str = '1m', limit: int = 100) -> List[float]:
        """
        Fetch kline data from Backpack Exchange
        
        Args:
            api_client: Backpack API client instance
            symbol: Trading symbol (default: BTC-USDT)
            interval: Kline interval (default: 1m)
            limit: Number of klines to fetch
        
        Returns:
            List of closing prices
        """
        try:
            klines = api_client.get_klines(symbol, interval, limit)
            
            # Extract closing prices from kline data
            # Assuming kline format: [timestamp, open, high, low, close, volume]
            closing_prices = [float(kline[4]) for kline in klines]
            
            return closing_prices
            
        except Exception as e:
            logger.error(f"Failed to fetch Backpack klines: {e}")
            return []
    
    def get_current_rsi(self, source: str = 'binance', api_client=None, symbol: str = None) -> Tuple[Optional[float], float]:
        """
        Get current RSI value
        
        Args:
            source: Data source ('binance' or 'backpack')
            api_client: Backpack API client (required if source is 'backpack')
            symbol: Trading symbol
        
        Returns:
            Tuple of (RSI value, current price)
        """
        # Fetch price data
        if source == 'binance':
            prices = self.get_binance_klines(
                symbol=symbol or 'BTCUSDT',
                interval='1m',
                limit=self.period + 50  # Get extra data for better accuracy
            )
        else:  # backpack
            if not api_client:
                logger.error("Backpack API client is required for Backpack data source")
                return None, 0
            
            prices = self.get_backpack_klines(
                api_client,
                symbol=symbol or 'BTC-USDT',
                interval='1m',
                limit=self.period + 50
            )
        
        if not prices:
            return None, 0
        
        # Calculate RSI
        rsi = self.calculate_rsi(prices)
        current_price = prices[-1] if prices else 0
        
        # Store in history
        if rsi is not None:
            self.rsi_history.append({
                'timestamp': datetime.now(),
                'rsi': rsi,
                'price': current_price
            })
            
            # Keep only last 1000 entries
            if len(self.rsi_history) > 1000:
                self.rsi_history = self.rsi_history[-1000:]
        
        return rsi, current_price
    
    def get_rsi_stats(self) -> Dict:
        """
        Get RSI statistics from history
        
        Returns:
            Dictionary with RSI statistics
        """
        if not self.rsi_history:
            return {}
        
        rsi_values = [entry['rsi'] for entry in self.rsi_history]
        
        return {
            'current': rsi_values[-1] if rsi_values else None,
            'min': min(rsi_values),
            'max': max(rsi_values),
            'avg': sum(rsi_values) / len(rsi_values),
            'count': len(rsi_values)
        }