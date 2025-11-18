#!/usr/bin/env python3
"""
测试GUI界面（使用模拟数据）
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime
import schedule
from data_storage import DataStorage
import random

class BTCMonitorGUITest:
    def __init__(self, root):
        self.root = root
        self.root.title("BTC价差监控系统 - 测试模式")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # 初始化组件
        self.data_storage = DataStorage('btc_price_data_test.csv')
        self.monitoring = False
        self.monitor_thread = None
        
        # 模拟价格数据
        self.base_price = 95000.0
        self.current_prices = {
            'backpack': self.base_price + random.uniform(-500, 500),
            'lighter': self.base_price + random.uniform(-500, 500),
            'difference': None,
            'difference_percent': None
        }
        self._calculate_difference()
        
        self.setup_ui()
        self.load_history_data()
        
        # 启动时立即更新一次
        self.update_price_display()
    
    def _calculate_difference(self):
        """计算价差"""
        if self.current_prices['backpack'] and self.current_prices['lighter']:
            self.current_prices['difference'] = self.current_prices['backpack'] - self.current_prices['lighter']
            if self.current_prices['lighter'] != 0:
                self.current_prices['difference_percent'] = (self.current_prices['difference'] / self.current_prices['lighter']) * 100
    
    def setup_ui(self):
        """设置UI界面"""
        # 标题
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="BTC价差监控系统 (测试模式)",
            font=('Arial', 20, 'bold'),
            bg='#2c3e50',
            fg='white'
        )
        title_label.pack(pady=15)
        
        # 实时价格显示区域
        price_frame = tk.Frame(self.root, bg='#ecf0f1', padx=20, pady=20)
        price_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Backpack价格
        backpack_frame = tk.Frame(price_frame, bg='#3498db', padx=20, pady=15)
        backpack_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        tk.Label(
            backpack_frame,
            text="Backpack交易所",
            font=('Arial', 12, 'bold'),
            bg='#3498db',
            fg='white'
        ).pack()
        
        self.backpack_label = tk.Label(
            backpack_frame,
            text="$0.00",
            font=('Arial', 18, 'bold'),
            bg='#3498db',
            fg='white'
        )
        self.backpack_label.pack(pady=5)
        
        # Lighter价格
        lighter_frame = tk.Frame(price_frame, bg='#e74c3c', padx=20, pady=15)
        lighter_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        tk.Label(
            lighter_frame,
            text="Lighter交易所",
            font=('Arial', 12, 'bold'),
            bg='#e74c3c',
            fg='white'
        ).pack()
        
        self.lighter_label = tk.Label(
            lighter_frame,
            text="$0.00",
            font=('Arial', 18, 'bold'),
            bg='#e74c3c',
            fg='white'
        )
        self.lighter_label.pack(pady=5)
        
        # 价差显示
        diff_frame = tk.Frame(price_frame, bg='#27ae60', padx=20, pady=15)
        diff_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        tk.Label(
            diff_frame,
            text="价差",
            font=('Arial', 12, 'bold'),
            bg='#27ae60',
            fg='white'
        ).pack()
        
        self.diff_label = tk.Label(
            diff_frame,
            text="$0.00 (0.00%)",
            font=('Arial', 18, 'bold'),
            bg='#27ae60',
            fg='white'
        )
        self.diff_label.pack(pady=5)
        
        # 控制按钮区域
        control_frame = tk.Frame(self.root, bg='#f0f0f0', padx=20, pady=10)
        control_frame.pack(fill=tk.X)
        
        self.start_button = tk.Button(
            control_frame,
            text="开始监控",
            command=self.start_monitoring,
            bg='#27ae60',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10,
            relief=tk.RAISED,
            cursor='hand2'
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(
            control_frame,
            text="停止监控",
            command=self.stop_monitoring,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10,
            relief=tk.RAISED,
            cursor='hand2',
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.refresh_button = tk.Button(
            control_frame,
            text="模拟更新",
            command=self.simulate_update,
            bg='#3498db',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10,
            relief=tk.RAISED,
            cursor='hand2'
        )
        self.refresh_button.pack(side=tk.LEFT, padx=5)
        
        # 状态标签
        self.status_label = tk.Label(
            control_frame,
            text="状态: 测试模式 (使用模拟数据)",
            font=('Arial', 10),
            bg='#f0f0f0',
            fg='#7f8c8d'
        )
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # 历史数据表格
        table_frame = tk.Frame(self.root, bg='#f0f0f0', padx=10, pady=10)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            table_frame,
            text="历史价差数据（每小时更新）",
            font=('Arial', 14, 'bold'),
            bg='#f0f0f0'
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # 创建表格
        columns = ('时间', 'Backpack价格', 'Lighter价格', '价差(USD)', '价差百分比(%)')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # 设置列标题和宽度
        self.tree.heading('时间', text='时间')
        self.tree.heading('Backpack价格', text='Backpack价格')
        self.tree.heading('Lighter价格', text='Lighter价格')
        self.tree.heading('价差(USD)', text='价差(USD)')
        self.tree.heading('价差百分比(%)', text='价差百分比(%)')
        
        self.tree.column('时间', width=180)
        self.tree.column('Backpack价格', width=150)
        self.tree.column('Lighter价格', width=150)
        self.tree.column('价差(USD)', width=150)
        self.tree.column('价差百分比(%)', width=150)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def update_price_display(self):
        """更新价格显示"""
        if self.current_prices['backpack']:
            self.backpack_label.config(text=f"${self.current_prices['backpack']:,.2f}")
        else:
            self.backpack_label.config(text="获取中...")
        
        if self.current_prices['lighter']:
            self.lighter_label.config(text=f"${self.current_prices['lighter']:,.2f}")
        else:
            self.lighter_label.config(text="获取中...")
        
        if self.current_prices['difference'] is not None:
            diff_text = f"${self.current_prices['difference']:,.2f}"
            if self.current_prices['difference_percent'] is not None:
                diff_text += f"\n({self.current_prices['difference_percent']:.4f}%)"
            self.diff_label.config(text=diff_text)
        else:
            self.diff_label.config(text="计算中...")
    
    def simulate_update(self):
        """模拟价格更新"""
        # 生成新的模拟价格
        self.current_prices['backpack'] = self.base_price + random.uniform(-500, 500)
        self.current_prices['lighter'] = self.base_price + random.uniform(-500, 500)
        self._calculate_difference()
        
        self.update_price_display()
        
        # 如果监控中，保存数据
        if self.monitoring:
            self.data_storage.save_price_data(
                self.current_prices['backpack'],
                self.current_prices['lighter'],
                self.current_prices['difference'],
                self.current_prices['difference_percent']
            )
            self.load_history_data()
        
        self.status_label.config(
            text=f"状态: 最后更新 {datetime.now().strftime('%H:%M:%S')} (模拟数据)",
            fg='#27ae60'
        )
    
    def start_monitoring(self):
        """开始监控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # 立即保存一次当前数据
        self.data_storage.save_price_data(
            self.current_prices['backpack'],
            self.current_prices['lighter'],
            self.current_prices['difference'],
            self.current_prices['difference_percent']
        )
        self.load_history_data()
        
        # 启动定时任务线程
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.status_label.config(text="状态: 监控已启动（每小时更新）", fg='#27ae60')
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="状态: 监控已停止", fg='#7f8c8d')
    
    def monitor_loop(self):
        """监控循环"""
        schedule.clear()
        schedule.every().hour.do(self.scheduled_update)
        
        while self.monitoring:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    
    def scheduled_update(self):
        """定时更新"""
        if self.monitoring:
            self.root.after(0, self.simulate_update)
    
    def load_history_data(self, limit=50):
        """加载历史数据到表格"""
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 加载数据
        df = self.data_storage.load_data(limit=limit)
        
        # 插入数据（从最新到最旧）
        for idx in reversed(df.index):
            row = df.loc[idx]
            self.tree.insert('', 'end', values=(
                row['时间'],
                row['Backpack价格'],
                row['Lighter价格'],
                row['价差(USD)'],
                row['价差百分比(%)']
            ))


def main():
    root = tk.Tk()
    app = BTCMonitorGUITest(root)
    root.mainloop()


if __name__ == "__main__":
    main()
