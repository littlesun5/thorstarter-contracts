#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BTC价差监控工具
监控 Backpack Exchange 和 Lighter 交易所的BTC价格差异
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import requests
import json
import threading
import time
from datetime import datetime
import pandas as pd
from typing import Optional, Dict, Tuple


class BTCPriceMonitor:
    """BTC价格监控器"""
    
    def __init__(self):
        self.backpack_price: Optional[float] = None
        self.lighter_price: Optional[float] = None
        self.price_diff: Optional[float] = None
        self.price_history = []
        self.running = False
        self.last_hourly_record = None
        
    def get_backpack_price(self) -> Optional[float]:
        """获取Backpack交易所的BTC价格"""
        try:
            # Backpack API endpoint
            url = "https://api.backpack.exchange/api/v1/ticker"
            params = {"symbol": "BTC_USDC"}
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                # 使用最后成交价或中间价
                if isinstance(data, dict):
                    price = float(data.get('lastPrice', 0))
                    if price > 0:
                        return price
                    # 尝试使用买卖价的中间价
                    bid = float(data.get('bidPrice', 0))
                    ask = float(data.get('askPrice', 0))
                    if bid > 0 and ask > 0:
                        return (bid + ask) / 2
        except Exception as e:
            print(f"获取Backpack价格失败: {e}")
        return None
    
    def get_lighter_price(self) -> Optional[float]:
        """获取Lighter交易所的BTC价格"""
        # 方法1: 尝试Lighter官方API
        try:
            url = "https://api.lighter.xyz/v1/tickers"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    for ticker in data:
                        symbol = ticker.get('symbol', '')
                        if 'BTC' in symbol.upper():
                            price = float(ticker.get('last', 0))
                            if price > 0:
                                return price
                elif isinstance(data, dict):
                    btc_ticker = data.get('BTCUSD', {})
                    price = float(btc_ticker.get('last', 0))
                    if price > 0:
                        return price
        except Exception as e:
            print(f"Lighter API方法1失败: {e}")
        
        # 方法2: 尝试使用CoinGecko作为参考价格
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {"ids": "bitcoin", "vs_currencies": "usd"}
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                price = float(data.get('bitcoin', {}).get('usd', 0))
                if price > 0:
                    print("使用CoinGecko参考价格（作为Lighter替代）")
                    return price
        except Exception as e:
            print(f"CoinGecko备用方法失败: {e}")
        
        # 方法3: 尝试Binance API作为备用
        try:
            url = "https://api.binance.com/api/v3/ticker/price"
            params = {"symbol": "BTCUSDT"}
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                price = float(data.get('price', 0))
                if price > 0:
                    print("使用Binance参考价格（作为Lighter替代）")
                    return price
        except Exception as e:
            print(f"Binance备用方法失败: {e}")
            
        return None
    
    def update_prices(self) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """更新价格并计算价差"""
        self.backpack_price = self.get_backpack_price()
        self.lighter_price = self.get_lighter_price()
        
        if self.backpack_price and self.lighter_price:
            self.price_diff = self.backpack_price - self.lighter_price
        else:
            self.price_diff = None
            
        return self.backpack_price, self.lighter_price, self.price_diff
    
    def should_record_hourly(self) -> bool:
        """检查是否应该记录每小时数据"""
        current_time = datetime.now()
        if self.last_hourly_record is None:
            return True
        
        time_diff = (current_time - self.last_hourly_record).total_seconds()
        return time_diff >= 3600  # 1小时 = 3600秒
    
    def record_price(self):
        """记录价格数据"""
        if self.backpack_price and self.lighter_price and self.price_diff is not None:
            record = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'backpack': self.backpack_price,
                'lighter': self.lighter_price,
                'diff': self.price_diff,
                'diff_percent': (self.price_diff / self.lighter_price * 100) if self.lighter_price else 0
            }
            self.price_history.append(record)
            self.last_hourly_record = datetime.now()
            return record
        return None


class BTCMonitorGUI:
    """BTC监控GUI界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("BTC价差监控工具")
        self.root.geometry("900x700")
        self.monitor = BTCPriceMonitor()
        self.update_thread = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI界面"""
        # 标题
        title_label = tk.Label(
            self.root, 
            text="BTC价差监控 (Backpack vs Lighter)", 
            font=("Arial", 16, "bold"),
            pady=10
        )
        title_label.pack()
        
        # 实时价格显示框架
        price_frame = tk.LabelFrame(self.root, text="实时价格", padx=10, pady=10)
        price_frame.pack(fill="x", padx=10, pady=5)
        
        # Backpack价格
        backpack_frame = tk.Frame(price_frame)
        backpack_frame.pack(fill="x", pady=2)
        tk.Label(backpack_frame, text="Backpack Exchange:", font=("Arial", 10, "bold"), width=20, anchor="w").pack(side="left")
        self.backpack_label = tk.Label(backpack_frame, text="--", font=("Arial", 12), fg="blue")
        self.backpack_label.pack(side="left")
        
        # Lighter价格
        lighter_frame = tk.Frame(price_frame)
        lighter_frame.pack(fill="x", pady=2)
        tk.Label(lighter_frame, text="Lighter:", font=("Arial", 10, "bold"), width=20, anchor="w").pack(side="left")
        self.lighter_label = tk.Label(lighter_frame, text="--", font=("Arial", 12), fg="green")
        self.lighter_label.pack(side="left")
        
        # 价差显示
        diff_frame = tk.Frame(price_frame)
        diff_frame.pack(fill="x", pady=2)
        tk.Label(diff_frame, text="价差:", font=("Arial", 10, "bold"), width=20, anchor="w").pack(side="left")
        self.diff_label = tk.Label(diff_frame, text="--", font=("Arial", 14, "bold"), fg="red")
        self.diff_label.pack(side="left")
        
        # 更新时间
        time_frame = tk.Frame(price_frame)
        time_frame.pack(fill="x", pady=2)
        tk.Label(time_frame, text="最后更新:", font=("Arial", 9), width=20, anchor="w").pack(side="left")
        self.time_label = tk.Label(time_frame, text="--", font=("Arial", 9))
        self.time_label.pack(side="left")
        
        # 控制按钮
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        self.start_button = tk.Button(
            button_frame, 
            text="开始监控", 
            command=self.start_monitoring,
            bg="green",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        )
        self.start_button.pack(side="left", padx=5)
        
        self.stop_button = tk.Button(
            button_frame, 
            text="停止监控", 
            command=self.stop_monitoring,
            bg="red",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5,
            state="disabled"
        )
        self.stop_button.pack(side="left", padx=5)
        
        self.refresh_button = tk.Button(
            button_frame, 
            text="立即刷新", 
            command=self.manual_refresh,
            bg="blue",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        )
        self.refresh_button.pack(side="left", padx=5)
        
        self.export_button = tk.Button(
            button_frame, 
            text="导出数据", 
            command=self.export_data,
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        )
        self.export_button.pack(side="left", padx=5)
        
        # 设置信息
        settings_frame = tk.LabelFrame(self.root, text="设置", padx=10, pady=5)
        settings_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(settings_frame, text="刷新间隔(秒):").pack(side="left")
        self.refresh_interval = tk.Entry(settings_frame, width=10)
        self.refresh_interval.insert(0, "10")
        self.refresh_interval.pack(side="left", padx=5)
        
        tk.Label(settings_frame, text="  记录间隔: 每1小时自动记录", fg="gray").pack(side="left")
        
        # 历史记录表格
        history_frame = tk.LabelFrame(self.root, text="历史记录 (每小时)", padx=10, pady=10)
        history_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 创建Treeview表格
        columns = ("时间", "Backpack", "Lighter", "价差", "价差%")
        self.tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=10)
        
        # 设置列标题
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 状态栏
        self.status_label = tk.Label(
            self.root, 
            text="就绪", 
            bd=1, 
            relief="sunken", 
            anchor="w"
        )
        self.status_label.pack(side="bottom", fill="x")
        
    def update_display(self):
        """更新显示"""
        backpack, lighter, diff = self.monitor.update_prices()
        
        # 更新价格显示
        if backpack:
            self.backpack_label.config(text=f"${backpack:,.2f}")
        else:
            self.backpack_label.config(text="获取失败")
            
        if lighter:
            self.lighter_label.config(text=f"${lighter:,.2f}")
        else:
            self.lighter_label.config(text="获取失败")
            
        if diff is not None:
            color = "red" if diff > 0 else "green"
            percent = (diff / lighter * 100) if lighter else 0
            self.diff_label.config(
                text=f"${diff:,.2f} ({percent:+.2f}%)",
                fg=color
            )
        else:
            self.diff_label.config(text="计算失败", fg="gray")
            
        # 更新时间
        self.time_label.config(text=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # 检查是否需要记录每小时数据
        if self.monitor.should_record_hourly():
            record = self.monitor.record_price()
            if record:
                self.add_record_to_tree(record)
                self.status_label.config(text=f"已记录数据: {record['timestamp']}")
        
    def add_record_to_tree(self, record):
        """添加记录到表格"""
        self.tree.insert("", 0, values=(
            record['timestamp'],
            f"${record['backpack']:,.2f}",
            f"${record['lighter']:,.2f}",
            f"${record['diff']:,.2f}",
            f"{record['diff_percent']:+.2f}%"
        ))
        
    def start_monitoring(self):
        """开始监控"""
        self.monitor.running = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.status_label.config(text="监控中...")
        
        def monitor_loop():
            while self.monitor.running:
                try:
                    self.update_display()
                    interval = int(self.refresh_interval.get())
                    for _ in range(interval * 10):  # 分成更小的间隔检查停止信号
                        if not self.monitor.running:
                            break
                        time.sleep(0.1)
                except Exception as e:
                    print(f"监控错误: {e}")
                    self.status_label.config(text=f"错误: {e}")
                    time.sleep(5)
        
        self.update_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.update_thread.start()
        
    def stop_monitoring(self):
        """停止监控"""
        self.monitor.running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.status_label.config(text="已停止")
        
    def manual_refresh(self):
        """手动刷新"""
        self.update_display()
        self.status_label.config(text="已刷新")
        
    def export_data(self):
        """导出数据到CSV"""
        if not self.monitor.price_history:
            self.status_label.config(text="没有数据可导出")
            return
            
        try:
            df = pd.DataFrame(self.monitor.price_history)
            filename = f"btc_price_diff_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            self.status_label.config(text=f"数据已导出到: {filename}")
        except Exception as e:
            self.status_label.config(text=f"导出失败: {e}")


def main():
    """主函数"""
    root = tk.Tk()
    app = BTCMonitorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
