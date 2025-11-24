"""
币安API封装（仅用于获取价格数据）
"""
import requests
from typing import List, Optional

class BinanceAPI:
    """币安API客户端（只读）"""
    
    def __init__(self):
        """初始化API客户端"""
        self.base_url = "https://api.binance.com"
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> Optional[List]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对符号（如BTCUSDT）
            interval: 时间间隔（1m, 5m, 15m, 1h等）
            limit: 数据条数
            
        Returns:
            K线数据列表
        """
        try:
            url = f"{self.base_url}/api/v3/klines"
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取币安K线数据错误: {e}")
            return None
    
    def get_ticker_price(self, symbol: str) -> Optional[float]:
        """
        获取最新价格
        
        Args:
            symbol: 交易对符号（如BTCUSDT）
            
        Returns:
            最新价格
        """
        try:
            url = f"{self.base_url}/api/v3/ticker/price"
            params = {"symbol": symbol}
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return float(data["price"])
        except Exception as e:
            print(f"获取币安价格错误: {e}")
            return None
