"""
Backpack Exchange API Client
Handles REST API calls for trading and account management
"""

import requests
import hmac
import hashlib
import time
import json
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)


class BackpackAPI:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        """
        Initialize Backpack Exchange API client
        
        Args:
            api_key: API key from Backpack Exchange
            api_secret: API secret from Backpack Exchange
            testnet: Use testnet if True, mainnet if False
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.backpack.exchange/api/v1" if not testnet else "https://api.testnet.backpack.exchange/api/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        })
    
    def _sign_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """
        Sign a request with HMAC-SHA256
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
        
        Returns:
            Signed headers
        """
        timestamp = str(int(time.time() * 1000))
        
        # Construct signature payload
        signature_payload = f"{timestamp}{method}{endpoint}"
        
        if params:
            query_string = urlencode(sorted(params.items()))
            signature_payload += f"?{query_string}"
        
        if data:
            signature_payload += json.dumps(data, separators=(',', ':'))
        
        # Create signature
        signature = hmac.new(
            self.api_secret.encode(),
            signature_payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return {
            'X-Timestamp': timestamp,
            'X-Signature': signature
        }
    
    def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """
        Make a signed request to the API
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body
        
        Returns:
            API response
        """
        url = f"{self.base_url}{endpoint}"
        
        # Sign the request
        signed_headers = self._sign_request(method, endpoint, params, data)
        headers = {**self.session.headers, **signed_headers}
        
        try:
            response = self.session.request(
                method,
                url,
                params=params,
                json=data,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise
    
    # Market Data Methods
    def get_ticker(self, symbol: str) -> Dict:
        """Get current ticker data for a symbol"""
        return self._request('GET', f'/ticker', params={'symbol': symbol})
    
    def get_orderbook(self, symbol: str, depth: int = 20) -> Dict:
        """Get orderbook for a symbol"""
        return self._request('GET', f'/depth', params={'symbol': symbol, 'limit': depth})
    
    def get_klines(self, symbol: str, interval: str = '1m', limit: int = 100) -> List:
        """
        Get kline/candlestick data
        
        Args:
            symbol: Trading symbol (e.g., 'BTC-USDT')
            interval: Kline interval (1m, 5m, 15m, 30m, 1h, 4h, 1d)
            limit: Number of klines to return
        
        Returns:
            List of kline data
        """
        return self._request('GET', '/klines', params={
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        })
    
    # Account Methods
    def get_account_balance(self) -> Dict:
        """Get account balance"""
        return self._request('GET', '/account')
    
    def get_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get open positions"""
        params = {'symbol': symbol} if symbol else {}
        return self._request('GET', '/positions', params=params)
    
    # Trading Methods
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        time_in_force: str = 'GTC',
        post_only: bool = False,
        reduce_only: bool = False
    ) -> Dict:
        """
        Place a new order
        
        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            order_type: 'limit' or 'market'
            quantity: Order quantity
            price: Order price (required for limit orders)
            time_in_force: Time in force (GTC, IOC, FOK)
            post_only: Post-only order
            reduce_only: Reduce-only order
        
        Returns:
            Order response
        """
        data = {
            'symbol': symbol,
            'side': side.lower(),
            'type': order_type.lower(),
            'quantity': quantity,
            'timeInForce': time_in_force
        }
        
        if order_type.lower() == 'limit':
            if price is None:
                raise ValueError("Price is required for limit orders")
            data['price'] = price
        
        if post_only:
            data['postOnly'] = True
        
        if reduce_only:
            data['reduceOnly'] = True
        
        return self._request('POST', '/order', data=data)
    
    def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """Cancel an order"""
        return self._request('DELETE', '/order', data={
            'orderId': order_id,
            'symbol': symbol
        })
    
    def cancel_all_orders(self, symbol: Optional[str] = None) -> Dict:
        """Cancel all open orders"""
        data = {'symbol': symbol} if symbol else {}
        return self._request('DELETE', '/orders', data=data)
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get open orders"""
        params = {'symbol': symbol} if symbol else {}
        return self._request('GET', '/orders', params=params)
    
    def get_order_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get order history"""
        params = {'limit': limit}
        if symbol:
            params['symbol'] = symbol
        return self._request('GET', '/orders/history', params=params)
    
    def get_trade_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get trade history"""
        params = {'limit': limit}
        if symbol:
            params['symbol'] = symbol
        return self._request('GET', '/trades', params=params)