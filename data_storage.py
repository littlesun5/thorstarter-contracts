"""
数据存储模块 - 存储和管理价差数据
"""
import csv
import os
from datetime import datetime
import pandas as pd
from pathlib import Path


class DataStorage:
    def __init__(self, data_file='btc_price_data.csv'):
        self.data_file = data_file
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """确保CSV文件存在，如果不存在则创建并写入表头"""
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    '时间', 'Backpack价格', 'Lighter价格', 
                    '价差(USD)', '价差百分比(%)'
                ])
    
    def save_price_data(self, backpack_price, lighter_price, difference, difference_percent):
        """保存价格数据到CSV文件"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(self.data_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                f"{backpack_price:.2f}" if backpack_price else "N/A",
                f"{lighter_price:.2f}" if lighter_price else "N/A",
                f"{difference:.2f}" if difference is not None else "N/A",
                f"{difference_percent:.4f}" if difference_percent is not None else "N/A"
            ])
    
    def load_data(self, limit=None):
        """加载历史数据"""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8')
            if limit:
                df = df.tail(limit)
            return df
        except Exception as e:
            print(f"加载数据时出错: {e}")
            return pd.DataFrame()
    
    def get_latest_data(self, count=10):
        """获取最新的N条数据"""
        return self.load_data(limit=count)
