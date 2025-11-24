"""
Backpack Exchange API封装
"""
import time
import hmac
import hashlib
import base64
import requests
import json
from typing import Dict, List, Optional
from urllib.parse import urlencode

class BackpackAPI:
    """Backpack交易所API客户端"""
    
    def __init__(self, api_key: str, secret_key: str):
        """
        初始化API客户端
        
        Args:
            api_key: API密钥
            secret_key: API密钥
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = "https://api.backpack.exchange"
        
    def _generate_signature(self, timestamp: int, window: int, params: str = "") -> str:
        """
        生成API签名
        
        Args:
            timestamp: 时间戳（毫秒）
            window: 时间窗口
            params: 请求参数
            
        Returns:
            签名字符串
        """
        instruction = f"instruction={params}&timestamp={timestamp}&window={window}" if params else f"timestamp={timestamp}&window={window}"
        signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode('utf-8'),
                instruction.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        return signature
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, signed: bool = False) -> Dict:
        """
        发送API请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            params: 请求参数
            signed: 是否需要签名
            
        Returns:
            响应数据
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        if signed:
            timestamp = int(time.time() * 1000)
            window = 5000
            params_str = json.dumps(params) if params else ""
            signature = self._generate_signature(timestamp, window, params_str)
            headers["X-Timestamp"] = str(timestamp)
            headers["X-Window"] = str(window)
            headers["X-Signature"] = signature
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=params)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, json=params)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API请求错误: {e}")
            return None
    
    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """
        获取ticker信息
        
        Args:
            symbol: 交易对符号
            
        Returns:
            ticker数据
        """
        return self._make_request("GET", f"/api/v1/ticker", {"symbol": symbol})
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> Optional[List]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对符号
            interval: 时间间隔（1m, 5m, 15m, 1h等）
            limit: 数据条数
            
        Returns:
            K线数据列表
        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        return self._make_request("GET", "/api/v1/klines", params)
    
    def get_balance(self) -> Optional[Dict]:
        """获取账户余额"""
        return self._make_request("GET", "/api/v1/capital", signed=True)
    
    def get_open_orders(self, symbol: str) -> Optional[List]:
        """
        获取当前挂单
        
        Args:
            symbol: 交易对符号
            
        Returns:
            挂单列表
        """
        return self._make_request("GET", "/api/v1/orders", {"symbol": symbol}, signed=True)
    
    def create_order(self, symbol: str, side: str, order_type: str, 
                    quantity: float, price: float = None, 
                    time_in_force: str = "GTC") -> Optional[Dict]:
        """
        创建订单
        
        Args:
            symbol: 交易对符号
            side: 买卖方向（Buy/Sell）
            order_type: 订单类型（Limit/Market）
            quantity: 数量
            price: 价格（市价单可不填）
            time_in_force: 有效期类型
            
        Returns:
            订单信息
        """
        params = {
            "symbol": symbol,
            "side": side,
            "orderType": order_type,
            "quantity": str(quantity),
            "timeInForce": time_in_force
        }
        
        if price is not None and order_type == "Limit":
            params["price"] = str(price)
        
        return self._make_request("POST", "/api/v1/order", params, signed=True)
    
    def cancel_order(self, symbol: str, order_id: str) -> Optional[Dict]:
        """
        取消订单
        
        Args:
            symbol: 交易对符号
            order_id: 订单ID
            
        Returns:
            取消结果
        """
        params = {
            "symbol": symbol,
            "orderId": order_id
        }
        return self._make_request("DELETE", "/api/v1/order", params, signed=True)
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """
        获取持仓信息
        
        Args:
            symbol: 交易对符号
            
        Returns:
            持仓信息
        """
        positions = self._make_request("GET", "/api/v1/positions", signed=True)
        if positions:
            for pos in positions:
                if pos.get("symbol") == symbol:
                    return pos
        return None
