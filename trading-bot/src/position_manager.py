"""
Position Manager
Handles position tracking, scaling, and risk management
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents a trading position"""
    symbol: str
    side: str  # 'long' or 'short'
    entry_price: float
    quantity: float
    timestamp: datetime
    orders: List[Dict] = field(default_factory=list)
    realized_pnl: float = 0
    unrealized_pnl: float = 0
    
    @property
    def average_entry_price(self) -> float:
        """Calculate average entry price from all orders"""
        if not self.orders:
            return self.entry_price
        
        total_cost = sum(order['price'] * order['quantity'] for order in self.orders)
        total_quantity = sum(order['quantity'] for order in self.orders)
        
        return total_cost / total_quantity if total_quantity > 0 else 0
    
    @property
    def total_quantity(self) -> float:
        """Get total position quantity"""
        if not self.orders:
            return self.quantity
        return sum(order['quantity'] for order in self.orders)
    
    def calculate_pnl(self, current_price: float) -> float:
        """Calculate unrealized PnL"""
        if self.side == 'long':
            return (current_price - self.average_entry_price) * self.total_quantity
        else:  # short
            return (self.average_entry_price - current_price) * self.total_quantity


class PositionManager:
    def __init__(self, config: Dict):
        """
        Initialize Position Manager
        
        Args:
            config: Configuration dictionary with trading parameters
        """
        self.config = config
        self.positions = {}  # symbol -> Position
        self.last_order_time = {}  # symbol -> timestamp
        self.order_history = []
        
        # Extract config parameters
        self.initial_size = float(config.get('INITIAL_POSITION_SIZE', 0.03))
        self.scale_sizes = [float(x) for x in config.get('SCALE_IN_SIZES', '0.05,0.08,0.1,0.15,0.2,0.3').split(',')]
        self.scale_thresholds = [float(x) for x in config.get('SCALE_IN_THRESHOLDS', '150,250,500,800,1200,1500').split(',')]
        self.max_position = float(config.get('MAX_POSITION_SIZE', 2.0))
        self.stop_loss_usd = float(config.get('STOP_LOSS_USD', 1000))
        self.min_order_interval = int(config.get('MIN_ORDER_INTERVAL', 20))
        self.market_fee = float(config.get('MARKET_FEE', 0.0002))
        self.limit_fee = float(config.get('LIMIT_FEE', 0))
    
    def can_place_order(self, symbol: str) -> bool:
        """
        Check if enough time has passed since last order
        
        Args:
            symbol: Trading symbol
        
        Returns:
            True if can place order, False otherwise
        """
        if symbol not in self.last_order_time:
            return True
        
        time_since_last = (datetime.now() - self.last_order_time[symbol]).seconds
        return time_since_last >= self.min_order_interval
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get current position for a symbol"""
        return self.positions.get(symbol)
    
    def has_position(self, symbol: str) -> bool:
        """Check if there's an open position"""
        return symbol in self.positions
    
    def get_position_size(self, symbol: str) -> float:
        """Get current position size"""
        position = self.get_position(symbol)
        return position.total_quantity if position else 0
    
    def should_scale_in(self, symbol: str, current_price: float) -> Tuple[bool, float]:
        """
        Check if should scale into position based on price movement
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
        
        Returns:
            Tuple of (should_scale, order_size)
        """
        position = self.get_position(symbol)
        if not position:
            return False, 0
        
        # Check if we've hit max position size
        if position.total_quantity >= self.max_position:
            logger.info(f"Max position size reached for {symbol}: {position.total_quantity} BTC")
            return False, 0
        
        # Calculate price movement from average entry
        avg_entry = position.average_entry_price
        price_move = abs(current_price - avg_entry)
        
        # Determine which threshold we've crossed
        scale_level = len(position.orders) - 1  # -1 because initial order is at index 0
        
        if scale_level >= len(self.scale_thresholds):
            return False, 0
        
        # Check if price has moved enough for next scale-in
        threshold = self.scale_thresholds[scale_level] if scale_level >= 0 else 0
        
        if price_move >= threshold:
            # Ensure we haven't already scaled at this level
            if scale_level < len(self.scale_sizes):
                next_size = self.scale_sizes[scale_level]
                
                # Check if adding this size would exceed max position
                if position.total_quantity + next_size <= self.max_position:
                    return True, next_size
        
        return False, 0
    
    def should_close_position(self, symbol: str, current_price: float) -> Tuple[bool, str]:
        """
        Check if position should be closed (profit target or stop loss)
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
        
        Returns:
            Tuple of (should_close, reason)
        """
        position = self.get_position(symbol)
        if not position:
            return False, ""
        
        # Calculate PnL
        pnl = position.calculate_pnl(current_price)
        
        # Check stop loss
        if pnl <= -self.stop_loss_usd:
            return True, f"STOP_LOSS: PnL ${pnl:.2f} exceeds stop loss ${self.stop_loss_usd}"
        
        # Check if profit covers fees
        # Calculate total fees for opening and closing
        total_quantity = position.total_quantity
        open_fees = total_quantity * current_price * self.market_fee
        close_fees = total_quantity * current_price * self.market_fee
        total_fees = open_fees + close_fees
        
        # Close if profit covers fees with some buffer (10% extra)
        if pnl > total_fees * 1.1:
            return True, f"TAKE_PROFIT: PnL ${pnl:.2f} covers fees ${total_fees:.2f}"
        
        return False, ""
    
    def open_position(self, symbol: str, side: str, price: float, quantity: float) -> Position:
        """
        Open a new position
        
        Args:
            symbol: Trading symbol
            side: 'long' or 'short'
            price: Entry price
            quantity: Position quantity
        
        Returns:
            Created position
        """
        position = Position(
            symbol=symbol,
            side=side,
            entry_price=price,
            quantity=quantity,
            timestamp=datetime.now(),
            orders=[{
                'price': price,
                'quantity': quantity,
                'timestamp': datetime.now(),
                'type': 'initial'
            }]
        )
        
        self.positions[symbol] = position
        self.last_order_time[symbol] = datetime.now()
        
        logger.info(f"Opened {side} position for {symbol}: {quantity} BTC @ ${price:.2f}")
        
        return position
    
    def add_to_position(self, symbol: str, price: float, quantity: float) -> bool:
        """
        Add to existing position (scale in)
        
        Args:
            symbol: Trading symbol
            price: Entry price for new order
            quantity: Additional quantity
        
        Returns:
            True if successful
        """
        position = self.get_position(symbol)
        if not position:
            logger.error(f"No position found for {symbol}")
            return False
        
        # Check max position size
        if position.total_quantity + quantity > self.max_position:
            logger.warning(f"Cannot add {quantity} BTC - would exceed max position size")
            return False
        
        # Add order to position
        position.orders.append({
            'price': price,
            'quantity': quantity,
            'timestamp': datetime.now(),
            'type': 'scale_in'
        })
        
        self.last_order_time[symbol] = datetime.now()
        
        logger.info(f"Scaled into {position.side} position for {symbol}: "
                   f"+{quantity} BTC @ ${price:.2f} (Total: {position.total_quantity} BTC)")
        
        return True
    
    def close_position(self, symbol: str, price: float, reason: str = "") -> Optional[float]:
        """
        Close a position
        
        Args:
            symbol: Trading symbol
            price: Closing price
            reason: Reason for closing
        
        Returns:
            Realized PnL
        """
        position = self.get_position(symbol)
        if not position:
            logger.error(f"No position found for {symbol}")
            return None
        
        # Calculate final PnL
        final_pnl = position.calculate_pnl(price)
        
        # Record in history
        self.order_history.append({
            'symbol': symbol,
            'side': position.side,
            'entry_price': position.average_entry_price,
            'exit_price': price,
            'quantity': position.total_quantity,
            'pnl': final_pnl,
            'reason': reason,
            'timestamp': datetime.now()
        })
        
        # Remove position
        del self.positions[symbol]
        
        logger.info(f"Closed {position.side} position for {symbol}: "
                   f"{position.total_quantity} BTC @ ${price:.2f} "
                   f"PnL: ${final_pnl:.2f} ({reason})")
        
        return final_pnl
    
    def get_total_exposure(self) -> float:
        """Get total position size across all positions"""
        return sum(pos.total_quantity for pos in self.positions.values())
    
    def get_position_summary(self) -> Dict:
        """Get summary of all positions"""
        summary = {
            'positions': [],
            'total_exposure': 0,
            'total_pnl': 0
        }
        
        for symbol, position in self.positions.items():
            summary['positions'].append({
                'symbol': symbol,
                'side': position.side,
                'quantity': position.total_quantity,
                'avg_entry': position.average_entry_price,
                'unrealized_pnl': position.unrealized_pnl,
                'orders_count': len(position.orders)
            })
            summary['total_exposure'] += position.total_quantity
            summary['total_pnl'] += position.unrealized_pnl
        
        return summary