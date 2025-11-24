"""
Trading Bot Package
RSI-based automated trading bot for Backpack Exchange
"""

__version__ = "1.0.0"
__author__ = "Trading Bot"

from .backpack_api import BackpackAPI
from .rsi_calculator import RSICalculator
from .position_manager import PositionManager, Position
from .trading_bot import TradingBot

__all__ = [
    'BackpackAPI',
    'RSICalculator',
    'PositionManager',
    'Position',
    'TradingBot'
]