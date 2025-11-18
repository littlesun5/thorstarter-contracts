"""
BTC价差监控程序 - 带GUI界面
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime
import schedule
from price_fetcher import PriceFetcher
from data_storage import DataStorage


class BTCMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("BTC价差监控系统")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # 初始化组件
        self.price_fetcher = PriceFetcher()
        self.data_storage = DataStorage()
        self.monitoring = False
        self.monitor_thread = None
        
        # 当前价格数据
        self.current_prices = {
            'backpack': None,
            'lighter': None,
            'difference': None,
            'difference_percent': None
        }
        
        self.setup_ui()
        self.load_history_data()
        
        # 启动时立即获取一次价格
        self.update_prices()
    
    def setup_ui(self):
        """设置UI界面"""
        # 标题
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="BTC价差监控系统",
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
            text="立即刷新",
            command=self.update_prices,
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
            text="状态: 就绪",
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
    
    def update_prices(self):
        """更新价格数据"""
        self.status_label.config(text="状态: 正在获取价格...", fg='#3498db')
        self.root.update()
        
        try:
            prices = self.price_fetcher.get_prices()
            self.current_prices = prices
            
            # 更新显示
            self.update_price_display()
            
            # 如果监控中，保存数据
            if self.monitoring:
                self.data_storage.save_price_data(
                    prices['backpack'],
                    prices['lighter'],
                    prices['difference'],
                    prices['difference_percent']
                )
                self.load_history_data()
            
            self.status_label.config(
                text=f"状态: 最后更新 {datetime.now().strftime('%H:%M:%S')}",
                fg='#27ae60'
            )
            
        except Exception as e:
            self.status_label.config(text=f"状态: 获取价格失败 - {str(e)}", fg='#e74c3c')
            messagebox.showerror("错误", f"获取价格时出错: {str(e)}")
    
    def start_monitoring(self):
        """开始监控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # 立即保存一次当前数据
        if self.current_prices['backpack'] and self.current_prices['lighter']:
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
            self.root.after(0, self.update_prices)
    
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
    
    def on_closing(self):
        """关闭程序时的清理"""
        self.monitoring = False
        if self.price_fetcher:
            self.price_fetcher.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = BTCMonitorGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
