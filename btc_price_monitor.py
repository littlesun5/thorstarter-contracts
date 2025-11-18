#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BTC价格监控脚本
监控Backpack和Lighter两个交易所的BTC价格，计算价差并每小时记录
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
from bs4 import BeautifulSoup
import threading
import time
from datetime import datetime
import pandas as pd
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class BTCPriceMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("BTC价格监控 - Backpack vs Lighter")
        self.root.geometry("900x700")
        
        # 数据存储
        self.price_history = []
        self.data_file = "btc_price_data.json"
        self.is_running = False
        self.monitor_thread = None
        
        # 当前价格
        self.backpack_price = 0.0
        self.lighter_price = 0.0
        self.price_difference = 0.0
        self.price_difference_percent = 0.0
        
        # 初始化Selenium WebDriver
        self.driver = None
        self.init_selenium()
        
        # 加载历史数据
        self.load_history()
        
        # 创建GUI
        self.create_gui()
        
        # 立即获取一次价格
        self.fetch_prices()
        
    def init_selenium(self):
        """初始化Selenium WebDriver（无头模式）"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            # 尝试使用webdriver-manager（如果已安装）
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                print("使用webdriver-manager自动管理ChromeDriver")
            except ImportError:
                # 如果没有webdriver-manager，尝试系统PATH中的chromedriver
                # 或者尝试当前目录下的chromedriver
                try:
                    self.driver = webdriver.Chrome(options=chrome_options)
                except:
                    # 尝试当前目录
                    import os
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    chromedriver_path = os.path.join(current_dir, 'chromedriver')
                    if os.path.exists(chromedriver_path) or os.path.exists(chromedriver_path + '.exe'):
                        from selenium.webdriver.chrome.service import Service
                        service = Service(chromedriver_path if os.path.exists(chromedriver_path) else chromedriver_path + '.exe')
                        self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    else:
                        raise
        except Exception as e:
            print(f"警告: 无法初始化Chrome WebDriver: {e}")
            print("将尝试使用API方式获取价格")
            print("提示: 安装webdriver-manager可以自动管理ChromeDriver: pip install webdriver-manager")
            self.driver = None
    
    def fetch_backpack_price(self):
        """从Backpack交易所获取BTC价格"""
        try:
            # 首先尝试使用API（更快更可靠）
            try:
                api_url = "https://api.backpack.exchange/api/v1/ticker"
                response = requests.get(api_url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                if response.status_code == 200:
                    data = response.json()
                    # 查找BTC相关的ticker
                    for ticker in data:
                        symbol = ticker.get('symbol', '')
                        if 'BTC' in symbol and 'USD' in symbol:
                            price = float(ticker.get('lastPrice', 0))
                            if 10000 < price < 200000:  # 合理的BTC价格范围
                                return price
            except Exception as api_error:
                print(f"Backpack API错误: {api_error}")
            
            # 如果API失败，使用Selenium
            if self.driver:
                try:
                    self.driver.get("https://backpack.exchange/trade/BTC_USD_PERP")
                    time.sleep(5)  # 等待页面加载
                    
                    # 尝试多种可能的选择器
                    price_selectors = [
                        (By.XPATH, "//span[contains(@class, 'price')]"),
                        (By.XPATH, "//div[contains(@class, 'price')]"),
                        (By.XPATH, "//span[contains(text(), '$')]"),
                        (By.XPATH, "//div[contains(@class, 'ticker')]//span"),
                        (By.CSS_SELECTOR, "[class*='price']"),
                    ]
                    
                    for by, selector in price_selectors:
                        try:
                            elements = self.driver.find_elements(by, selector)
                            for element in elements:
                                price_text = element.text
                                if price_text and '$' in price_text:
                                    import re
                                    price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                                    if price_match:
                                        price = float(price_match.group().replace(',', ''))
                                        if 10000 < price < 200000:
                                            return price
                        except:
                            continue
                    
                    # 如果上述方法都失败，尝试从页面源码中提取
                    page_source = self.driver.page_source
                    import re
                    price_patterns = [
                        r'"price":\s*([\d.]+)',
                        r'"lastPrice":\s*([\d.]+)',
                        r'"markPrice":\s*([\d.]+)',
                        r'BTC_USD_PERP["\s]*:[\s]*([\d.]+)',
                        r'BTC.*?USD.*?(\d{4,6}\.?\d*)',
                    ]
                    for pattern in price_patterns:
                        matches = re.findall(pattern, page_source)
                        for match in matches:
                            try:
                                price = float(match)
                                if 10000 < price < 200000:
                                    return price
                            except:
                                continue
                except Exception as e:
                    print(f"Backpack Selenium解析错误: {e}")
            
            return None
        except Exception as e:
            print(f"获取Backpack价格错误: {e}")
            return None
    
    def fetch_lighter_price(self):
        """从Lighter交易所获取BTC价格"""
        try:
            # 首先尝试使用API（更快更可靠）
            try:
                api_urls = [
                    "https://api.lighter.xyz/v1/markets",
                    "https://api.lighter.xyz/v1/ticker",
                ]
                for api_url in api_urls:
                    try:
                        response = requests.get(api_url, timeout=10, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        })
                        if response.status_code == 200:
                            data = response.json()
                            # 如果是列表，遍历查找BTC
                            if isinstance(data, list):
                                for market in data:
                                    symbol = market.get('symbol', '') or market.get('pair', '')
                                    if 'BTC' in symbol:
                                        price = float(market.get('lastPrice', 0) or market.get('price', 0))
                                        if 10000 < price < 200000:
                                            return price
                            # 如果是字典，直接查找
                            elif isinstance(data, dict):
                                if 'BTC' in str(data):
                                    for key, value in data.items():
                                        if 'BTC' in key and isinstance(value, (int, float)):
                                            if 10000 < value < 200000:
                                                return float(value)
                    except:
                        continue
            except Exception as api_error:
                print(f"Lighter API错误: {api_error}")
            
            # 如果API失败，使用Selenium
            if self.driver:
                try:
                    self.driver.get("https://app.lighter.xyz/trade/BTC")
                    time.sleep(5)  # 等待页面加载
                    
                    # 尝试多种可能的选择器
                    price_selectors = [
                        (By.XPATH, "//span[contains(@class, 'price')]"),
                        (By.XPATH, "//div[contains(@class, 'price')]"),
                        (By.XPATH, "//span[contains(text(), '$')]"),
                        (By.XPATH, "//div[contains(@class, 'ticker')]//span"),
                        (By.XPATH, "//div[contains(@class, 'market-price')]"),
                        (By.CSS_SELECTOR, "[class*='price']"),
                    ]
                    
                    for by, selector in price_selectors:
                        try:
                            elements = self.driver.find_elements(by, selector)
                            for element in elements:
                                price_text = element.text
                                if price_text and '$' in price_text:
                                    import re
                                    price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                                    if price_match:
                                        price = float(price_match.group().replace(',', ''))
                                        if 10000 < price < 200000:
                                            return price
                        except:
                            continue
                    
                    # 如果上述方法都失败，尝试从页面源码中提取
                    page_source = self.driver.page_source
                    import re
                    price_patterns = [
                        r'"price":\s*([\d.]+)',
                        r'"lastPrice":\s*([\d.]+)',
                        r'"markPrice":\s*([\d.]+)',
                        r'BTC["\s]*:[\s]*([\d.]+)',
                        r'BTC.*?(\d{4,6}\.?\d*)',
                    ]
                    for pattern in price_patterns:
                        matches = re.findall(pattern, page_source)
                        for match in matches:
                            try:
                                price = float(match)
                                if 10000 < price < 200000:
                                    return price
                            except:
                                continue
                except Exception as e:
                    print(f"Lighter Selenium解析错误: {e}")
            
            return None
        except Exception as e:
            print(f"获取Lighter价格错误: {e}")
            return None
    
    def fetch_prices(self):
        """获取两个交易所的价格"""
        backpack = self.fetch_backpack_price()
        lighter = self.fetch_lighter_price()
        
        if backpack and lighter:
            self.backpack_price = backpack
            self.lighter_price = lighter
            self.price_difference = abs(backpack - lighter)
            if lighter > 0:
                self.price_difference_percent = (self.price_difference / lighter) * 100
            
            # 记录数据
            record = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'backpack_price': backpack,
                'lighter_price': lighter,
                'difference': self.price_difference,
                'difference_percent': self.price_difference_percent
            }
            self.price_history.append(record)
            self.save_history()
            
            # 更新GUI
            self.update_gui()
            return True
        else:
            error_msg = []
            if not backpack:
                error_msg.append("无法获取Backpack价格")
                print("无法获取Backpack价格")
            if not lighter:
                error_msg.append("无法获取Lighter价格")
                print("无法获取Lighter价格")
            
            if error_msg:
                # 在GUI中显示错误信息
                self.update_time_label.config(text="获取失败: " + ", ".join(error_msg), foreground="red")
                # 3秒后恢复
                self.root.after(3000, lambda: self.update_time_label.config(foreground="gray"))
            
            return False
    
    def create_gui(self):
        """创建GUI界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="BTC价格监控", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, pady=10)
        
        # 实时价格显示区域
        price_frame = ttk.LabelFrame(main_frame, text="实时价格", padding="10")
        price_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)
        price_frame.columnconfigure(1, weight=1)
        
        # Backpack价格
        ttk.Label(price_frame, text="Backpack价格:", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.backpack_label = ttk.Label(price_frame, text="$0.00", font=("Arial", 12, "bold"), foreground="blue")
        self.backpack_label.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Lighter价格
        ttk.Label(price_frame, text="Lighter价格:", font=("Arial", 12)).grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.lighter_label = ttk.Label(price_frame, text="$0.00", font=("Arial", 12, "bold"), foreground="green")
        self.lighter_label.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # 价差
        ttk.Label(price_frame, text="价差:", font=("Arial", 12)).grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.difference_label = ttk.Label(price_frame, text="$0.00 (0.00%)", font=("Arial", 12, "bold"), foreground="red")
        self.difference_label.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        # 最后更新时间
        ttk.Label(price_frame, text="最后更新:", font=("Arial", 10)).grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.update_time_label = ttk.Label(price_frame, text="未更新", font=("Arial", 10), foreground="gray")
        self.update_time_label.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        
        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, pady=5)
        
        self.start_button = ttk.Button(button_frame, text="开始监控", command=self.start_monitoring)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="停止监控", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.refresh_button = ttk.Button(button_frame, text="立即刷新", command=self.fetch_prices)
        self.refresh_button.pack(side=tk.LEFT, padx=5)
        
        # 历史数据表格
        table_frame = ttk.LabelFrame(main_frame, text="历史价差记录（每小时）", padding="10")
        table_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # 创建表格
        columns = ('时间', 'Backpack价格', 'Lighter价格', '价差', '价差百分比')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # 设置列标题和宽度
        self.tree.heading('时间', text='时间')
        self.tree.heading('Backpack价格', text='Backpack价格 ($)')
        self.tree.heading('Lighter价格', text='Lighter价格 ($)')
        self.tree.heading('价差', text='价差 ($)')
        self.tree.heading('价差百分比', text='价差百分比 (%)')
        
        self.tree.column('时间', width=180)
        self.tree.column('Backpack价格', width=150)
        self.tree.column('Lighter价格', width=150)
        self.tree.column('价差', width=120)
        self.tree.column('价差百分比', width=120)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 更新表格数据
        self.update_table()
    
    def update_gui(self):
        """更新GUI显示"""
        # 更新价格标签
        self.backpack_label.config(text=f"${self.backpack_price:,.2f}")
        self.lighter_label.config(text=f"${self.lighter_price:,.2f}")
        self.difference_label.config(text=f"${self.price_difference:,.2f} ({self.price_difference_percent:.2f}%)")
        self.update_time_label.config(text=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # 更新表格
        self.update_table()
    
    def update_table(self):
        """更新历史数据表格"""
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 添加历史数据（按时间倒序，最新的在前）
        for record in reversed(self.price_history[-100:]):  # 只显示最近100条
            self.tree.insert('', 'end', values=(
                record['timestamp'],
                f"{record['backpack_price']:,.2f}",
                f"{record['lighter_price']:,.2f}",
                f"{record['difference']:,.2f}",
                f"{record['difference_percent']:.2f}"
            ))
    
    def start_monitoring(self):
        """开始监控"""
        if not self.is_running:
            self.is_running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            # 启动监控线程
            self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
            self.monitor_thread.start()
            
            messagebox.showinfo("提示", "监控已开始，将每小时自动记录一次价格数据")
    
    def stop_monitoring(self):
        """停止监控"""
        if self.is_running:
            self.is_running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            messagebox.showinfo("提示", "监控已停止")
    
    def monitor_loop(self):
        """监控循环（每小时执行一次）"""
        while self.is_running:
            # 等待1小时（3600秒）
            for _ in range(3600):
                if not self.is_running:
                    return
                time.sleep(1)
            
            # 每小时获取一次价格
            if self.is_running:
                self.fetch_prices()
    
    def save_history(self):
        """保存历史数据到文件"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.price_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存数据错误: {e}")
    
    def load_history(self):
        """从文件加载历史数据"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.price_history = json.load(f)
        except Exception as e:
            print(f"加载数据错误: {e}")
            self.price_history = []
    
    def on_closing(self):
        """关闭窗口时的处理"""
        self.is_running = False
        if self.driver:
            self.driver.quit()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = BTCPriceMonitor(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
