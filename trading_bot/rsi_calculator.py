"""
RSI计算模块
"""
import numpy as np
import pandas as pd
from typing import List

class RSICalculator:
    """RSI指标计算器"""
    
    def __init__(self, period: int = 14):
        """
        初始化RSI计算器
        
        Args:
            period: RSI计算周期，默认14
        """
        self.period = period
        self.price_history = []
    
    def add_price(self, price: float):
        """添加新的价格数据"""
        self.price_history.append(price)
        # 保留足够的历史数据用于RSI计算
        if len(self.price_history) > self.period + 100:
            self.price_history = self.price_history[-100:]
    
    def calculate_rsi(self, prices: List[float] = None) -> float:
        """
        计算RSI值
        
        Args:
            prices: 价格列表，如果为None则使用历史价格
            
        Returns:
            RSI值，如果数据不足返回None
        """
        if prices is None:
            prices = self.price_history
        
        if len(prices) < self.period + 1:
            return None
        
        # 转换为pandas Series
        prices_series = pd.Series(prices)
        
        # 计算价格变化
        delta = prices_series.diff()
        
        # 分离上涨和下跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 计算平均涨幅和跌幅（使用EMA）
        avg_gain = gain.ewm(span=self.period, adjust=False).mean()
        avg_loss = loss.ewm(span=self.period, adjust=False).mean()
        
        # 避免除零
        avg_loss = avg_loss.replace(0, 0.0001)
        
        # 计算RS和RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1])
    
    def get_current_rsi(self) -> float:
        """获取当前RSI值"""
        return self.calculate_rsi()
    
    def reset(self):
        """重置价格历史"""
        self.price_history = []
