#!/usr/bin/env python3
"""
BTC Price Monitor for Backpack and Lighter Exchanges
监控Backpack和Lighter交易所的BTC价差
"""

import requests
import time
import json
from datetime import datetime
import sys

try:
    from plyer import notification
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False
    print("警告: plyer未安装，将使用控制台输出代替弹窗提醒")
    print("安装方法: pip install plyer")

class BTCPriceMonitor:
    def __init__(self, high_threshold=80, low_threshold=10, check_interval=5):
        """
        初始化BTC价格监控器
        
        Args:
            high_threshold: 价差上限（美元）
            low_threshold: 价差下限（美元）
            check_interval: 检查间隔（秒）
        """
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold
        self.check_interval = check_interval
        
        # API endpoints
        self.backpack_api = "https://api.backpack.exchange/api/v1/ticker"
        self.lighter_api = "https://api.lighter.xyz/v1/ticker"
        
        self.last_alert_time = 0
        self.alert_cooldown = 60  # 避免频繁弹窗，设置1分钟冷却时间
        
    def get_backpack_btc_price(self):
        """获取Backpack的BTC价格"""
        try:
            # Backpack API - 获取BTC_USDC交易对
            response = requests.get(f"{self.backpack_api}?symbol=BTC_USDC", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # 尝试多种可能的价格字段
            price = None
            if isinstance(data, dict):
                price = float(data.get('lastPrice') or data.get('last') or data.get('price'))
            
            return price
        except Exception as e:
            print(f"获取Backpack价格失败: {e}")
            return None
    
    def get_lighter_btc_price(self):
        """获取Lighter的BTC价格"""
        try:
            # Lighter API - 获取BTC交易对数据
            response = requests.get(f"{self.lighter_api}/BTC_USDC", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # 解析价格数据
            price = None
            if isinstance(data, dict):
                if 'data' in data:
                    price = float(data['data'].get('lastPrice') or data['data'].get('last') or data['data'].get('price'))
                else:
                    price = float(data.get('lastPrice') or data.get('last') or data.get('price'))
            
            return price
        except Exception as e:
            print(f"获取Lighter价格失败: {e}")
            return None
    
    def show_alert(self, message, title="BTC价差警告"):
        """显示提醒"""
        current_time = time.time()
        
        # 检查冷却时间
        if current_time - self.last_alert_time < self.alert_cooldown:
            return
        
        self.last_alert_time = current_time
        
        if NOTIFICATIONS_AVAILABLE:
            try:
                notification.notify(
                    title=title,
                    message=message,
                    app_name='BTC Monitor',
                    timeout=10
                )
            except Exception as e:
                print(f"弹窗提醒失败: {e}")
                print(f"【警告】{message}")
        else:
            print("\n" + "="*60)
            print(f"【警告】{title}")
            print(message)
            print("="*60 + "\n")
    
    def calculate_spread(self, backpack_price, lighter_price):
        """计算价差"""
        return abs(backpack_price - lighter_price)
    
    def check_prices(self):
        """检查价格并判断是否需要提醒"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        backpack_price = self.get_backpack_btc_price()
        lighter_price = self.get_lighter_btc_price()
        
        if backpack_price is None or lighter_price is None:
            print(f"[{timestamp}] 无法获取价格数据")
            return
        
        spread = self.calculate_spread(backpack_price, lighter_price)
        
        # 显示当前价格信息
        print(f"[{timestamp}]")
        print(f"  Backpack: ${backpack_price:.2f}")
        print(f"  Lighter:  ${lighter_price:.2f}")
        print(f"  价差:     ${spread:.2f}")
        
        # 判断是否需要提醒
        if spread > self.high_threshold:
            message = (
                f"价差过大！\n"
                f"Backpack: ${backpack_price:.2f}\n"
                f"Lighter: ${lighter_price:.2f}\n"
                f"价差: ${spread:.2f} (> ${self.high_threshold})"
            )
            self.show_alert(message, "BTC价差过大警告")
            
        elif spread < self.low_threshold:
            message = (
                f"价差过小！\n"
                f"Backpack: ${backpack_price:.2f}\n"
                f"Lighter: ${lighter_price:.2f}\n"
                f"价差: ${spread:.2f} (< ${self.low_threshold})"
            )
            self.show_alert(message, "BTC价差过小警告")
        
        print()
    
    def run(self):
        """运行监控器"""
        print("="*60)
        print("BTC价格监控器已启动")
        print(f"监控交易所: Backpack 和 Lighter")
        print(f"价差阈值: > ${self.high_threshold} 或 < ${self.low_threshold}")
        print(f"检查间隔: {self.check_interval}秒")
        print("="*60)
        print()
        
        try:
            while True:
                self.check_prices()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            print("\n监控器已停止")
            sys.exit(0)

def main():
    """主函数"""
    # 配置参数
    HIGH_THRESHOLD = 80   # 价差上限（美元）
    LOW_THRESHOLD = 10    # 价差下限（美元）
    CHECK_INTERVAL = 5    # 检查间隔（秒）
    
    # 创建并运行监控器
    monitor = BTCPriceMonitor(
        high_threshold=HIGH_THRESHOLD,
        low_threshold=LOW_THRESHOLD,
        check_interval=CHECK_INTERVAL
    )
    
    monitor.run()

if __name__ == "__main__":
    main()
