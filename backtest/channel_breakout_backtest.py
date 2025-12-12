#!/usr/bin/env python3
"""
通道突破策略回测系统 (Channel Break Out Strategy Backtest)
基于币安数据，1分钟K线，5周期通道突破

策略规则：
- 价格突破5周期最高价上轨 -> 做多
- 价格突破5周期最低价下轨 -> 做空
- 反向突破平仓
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from tabulate import tabulate
import os

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class BinanceDataFetcher:
    """从币安获取K线数据"""
    
    # 尝试多个端点
    BASE_URLS = [
        "https://data-api.binance.vision/api/v3/klines",  # 历史数据API
        "https://api1.binance.com/api/v3/klines",
        "https://api2.binance.com/api/v3/klines", 
        "https://api3.binance.com/api/v3/klines",
        "https://api.binance.com/api/v3/klines",
    ]
    
    @staticmethod
    def fetch_klines(symbol: str, interval: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """
        获取币安K线数据
        
        Args:
            symbol: 交易对，如 'BTCUSDT'
            interval: K线周期，如 '1m'
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            DataFrame with OHLCV data
        """
        all_klines = []
        current_start = start_time
        working_url = None
        
        print(f"正在从币安获取 {symbol} {interval} K线数据...")
        print(f"时间范围: {start_time} 至 {end_time}")
        
        while current_start < end_time:
            params = {
                'symbol': symbol,
                'interval': interval,
                'startTime': int(current_start.timestamp() * 1000),
                'endTime': int(end_time.timestamp() * 1000),
                'limit': 1000
            }
            
            # 如果还没找到可用的URL，尝试所有URL
            if working_url is None:
                for url in BinanceDataFetcher.BASE_URLS:
                    try:
                        response = requests.get(url, params=params, timeout=10)
                        if response.status_code == 200:
                            working_url = url
                            print(f"  使用数据源: {url}")
                            break
                    except:
                        continue
                        
                if working_url is None:
                    print("所有币安API端点均不可用")
                    break
            
            try:
                response = requests.get(working_url, params=params, timeout=30)
                response.raise_for_status()
                klines = response.json()
                
                if not klines:
                    break
                    
                all_klines.extend(klines)
                
                # 更新开始时间为最后一条K线的结束时间
                last_close_time = klines[-1][6]
                current_start = datetime.fromtimestamp(last_close_time / 1000) + timedelta(milliseconds=1)
                
                print(f"  已获取 {len(all_klines)} 条K线数据...", end='\r')
                
            except requests.exceptions.RequestException as e:
                print(f"\n获取数据出错: {e}")
                # 尝试切换URL
                working_url = None
                continue
        
        print(f"\n共获取 {len(all_klines)} 条K线数据")
        
        if not all_klines:
            return pd.DataFrame()
        
        # 转换为DataFrame
        df = pd.DataFrame(all_klines, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
            'taker_buy_quote_volume', 'ignore'
        ])
        
        # 转换数据类型
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        df.set_index('open_time', inplace=True)
        
        return df


class SimulatedDataGenerator:
    """生成模拟数据（当无法获取真实数据时使用）"""
    
    @staticmethod
    def generate_btc_like_data(start_time: datetime, end_time: datetime, 
                                interval_minutes: int = 1,
                                start_price: float = 96000,
                                volatility: float = 0.0002) -> pd.DataFrame:
        """
        生成类似BTC走势的模拟数据
        基于TradingView图表中的实际价格范围（约89000-94000）
        """
        print("正在生成模拟K线数据...")
        
        # 计算需要的K线数量
        total_minutes = int((end_time - start_time).total_seconds() / 60)
        n_bars = total_minutes // interval_minutes
        
        # 生成时间序列
        times = pd.date_range(start=start_time, periods=n_bars, freq=f'{interval_minutes}min')
        
        # 使用随机游走生成价格，模拟从89000涨到94000的走势
        np.random.seed(42)  # 可重复的结果
        
        # 生成收益率
        returns = np.random.normal(0.000005, volatility, n_bars)  # 略微向上的趋势
        
        # 添加一些周期性波动
        for i in range(n_bars):
            hour_of_day = (i // 60) % 24
            if hour_of_day < 6:  # 亚洲时段波动较小
                returns[i] *= 0.8
            elif hour_of_day < 14:  # 欧洲时段
                returns[i] *= 1.2
            else:  # 美国时段波动较大
                returns[i] *= 1.3
        
        # 计算收盘价
        close_prices = start_price * np.cumprod(1 + returns)
        
        # 生成OHLC
        data = []
        for i in range(n_bars):
            close = close_prices[i]
            # 随机生成高低开收
            range_pct = abs(np.random.normal(0, volatility * 2))
            high = close * (1 + range_pct)
            low = close * (1 - range_pct)
            
            if i == 0:
                open_price = start_price
            else:
                open_price = close_prices[i-1]
            
            # 确保逻辑正确
            high = max(high, open_price, close)
            low = min(low, open_price, close)
            
            volume = np.random.uniform(10, 100)
            
            data.append({
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        df = pd.DataFrame(data, index=times)
        
        print(f"生成 {len(df)} 条模拟K线数据")
        print(f"价格范围: ${df['low'].min():,.2f} - ${df['high'].max():,.2f}")
        
        return df


class ChannelBreakoutStrategy:
    """5周期通道突破策略"""
    
    def __init__(self, period: int = 5, use_high_low: bool = True):
        """
        Args:
            period: 通道周期，默认5
            use_high_low: 是否使用最高/最低价判断突破（TradingView方式）
        """
        self.period = period
        self.use_high_low = use_high_low
    
    def calculate_channels(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算通道上下轨
        
        Args:
            df: 包含OHLC数据的DataFrame
            
        Returns:
            添加了通道数据的DataFrame
        """
        df = df.copy()
        
        # 计算5周期最高价和最低价（不包括当前K线）
        df['upper_channel'] = df['high'].shift(1).rolling(window=self.period).max()
        df['lower_channel'] = df['low'].shift(1).rolling(window=self.period).min()
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        
        信号规则 (TradingView方式):
        - 最高价突破上轨 -> 做多信号 (1)
        - 最低价突破下轨 -> 做空信号 (-1)
        
        Args:
            df: 包含通道数据的DataFrame
            
        Returns:
            添加了信号的DataFrame
        """
        df = df.copy()
        
        # 初始化信号列
        df['signal'] = 0
        
        if self.use_high_low:
            # TradingView方式：使用最高价/最低价判断突破
            # 突破上轨 -> 做多
            df.loc[df['high'] > df['upper_channel'], 'signal'] = 1
            
            # 突破下轨 -> 做空
            df.loc[df['low'] < df['lower_channel'], 'signal'] = -1
        else:
            # 收盘价方式
            df.loc[df['close'] > df['upper_channel'], 'signal'] = 1
            df.loc[df['close'] < df['lower_channel'], 'signal'] = -1
        
        return df


class ChannelBreakoutStrategyV2:
    """
    5周期通道突破策略 V2 - 更接近TradingView的实现
    
    使用Donchian Channel (唐奇安通道)的经典突破逻辑
    """
    
    def __init__(self, period: int = 5):
        self.period = period
    
    def calculate_channels(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算通道"""
        df = df.copy()
        
        # Donchian通道：过去N根K线的最高价和最低价
        df['upper_channel'] = df['high'].rolling(window=self.period).max().shift(1)
        df['lower_channel'] = df['low'].rolling(window=self.period).min().shift(1)
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号 - 使用价格突破通道的方式
        
        TradingView的Channel Breakout通常是：
        - 当前K线收盘价 > 上轨 -> 做多
        - 当前K线收盘价 < 下轨 -> 做空
        """
        df = df.copy()
        df['signal'] = 0
        
        # 使用close突破判断
        df.loc[df['close'] > df['upper_channel'], 'signal'] = 1
        df.loc[df['close'] < df['lower_channel'], 'signal'] = -1
        
        return df


class Backtester:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = 10000, position_size: float = 0.1, fee_rate: float = 0.0):
        """
        Args:
            initial_capital: 初始资金 (USD)
            position_size: 单次开仓数量 (BTC)
            fee_rate: 手续费率
        """
        self.initial_capital = initial_capital
        self.position_size = position_size
        self.fee_rate = fee_rate
        
        # 交易记录
        self.trades = []
        
        # 资金曲线
        self.equity_curve = []
        
    def run(self, df: pd.DataFrame) -> dict:
        """
        运行回测
        
        Args:
            df: 包含信号的DataFrame
            
        Returns:
            回测结果字典
        """
        capital = self.initial_capital
        position = 0  # 当前持仓: 1=多, -1=空, 0=空仓
        entry_price = 0
        entry_time = None
        trade_id = 0
        
        self.trades = []
        self.equity_curve = []
        
        print("\n开始回测...")
        
        for idx, row in df.iterrows():
            current_price = row['close']
            signal = row['signal']
            
            # 计算当前权益
            unrealized_pnl = 0
            if position == 1:
                unrealized_pnl = (current_price - entry_price) * self.position_size
            elif position == -1:
                unrealized_pnl = (entry_price - current_price) * self.position_size
            
            current_equity = capital + unrealized_pnl
            self.equity_curve.append({
                'time': idx,
                'equity': current_equity,
                'position': position
            })
            
            # 检查是否需要交易
            if pd.isna(signal):
                continue
            
            # 空仓时
            if position == 0:
                if signal == 1:  # 开多
                    position = 1
                    entry_price = current_price
                    entry_time = idx
                    trade_id += 1
                elif signal == -1:  # 开空
                    position = -1
                    entry_price = current_price
                    entry_time = idx
                    trade_id += 1
            
            # 持多仓时
            elif position == 1:
                if signal == -1:  # 平多，开空
                    # 平多
                    pnl = (current_price - entry_price) * self.position_size
                    fee = current_price * self.position_size * self.fee_rate * 2  # 开仓+平仓手续费
                    net_pnl = pnl - fee
                    capital += net_pnl
                    
                    self.trades.append({
                        'trade_id': trade_id,
                        'direction': 'LONG',
                        'entry_time': entry_time,
                        'entry_price': entry_price,
                        'exit_time': idx,
                        'exit_price': current_price,
                        'size': self.position_size,
                        'pnl': pnl,
                        'fee': fee,
                        'net_pnl': net_pnl,
                        'capital_after': capital
                    })
                    
                    # 开空
                    position = -1
                    entry_price = current_price
                    entry_time = idx
                    trade_id += 1
            
            # 持空仓时
            elif position == -1:
                if signal == 1:  # 平空，开多
                    # 平空
                    pnl = (entry_price - current_price) * self.position_size
                    fee = current_price * self.position_size * self.fee_rate * 2
                    net_pnl = pnl - fee
                    capital += net_pnl
                    
                    self.trades.append({
                        'trade_id': trade_id,
                        'direction': 'SHORT',
                        'entry_time': entry_time,
                        'entry_price': entry_price,
                        'exit_time': idx,
                        'exit_price': current_price,
                        'size': self.position_size,
                        'pnl': pnl,
                        'fee': fee,
                        'net_pnl': net_pnl,
                        'capital_after': capital
                    })
                    
                    # 开多
                    position = 1
                    entry_price = current_price
                    entry_time = idx
                    trade_id += 1
        
        # 处理未平仓位（按最后价格平仓）
        if position != 0 and len(df) > 0:
            last_row = df.iloc[-1]
            current_price = last_row['close']
            
            if position == 1:
                pnl = (current_price - entry_price) * self.position_size
                direction = 'LONG'
            else:
                pnl = (entry_price - current_price) * self.position_size
                direction = 'SHORT'
            
            fee = current_price * self.position_size * self.fee_rate * 2
            net_pnl = pnl - fee
            capital += net_pnl
            
            self.trades.append({
                'trade_id': trade_id,
                'direction': direction,
                'entry_time': entry_time,
                'entry_price': entry_price,
                'exit_time': df.index[-1],
                'exit_price': current_price,
                'size': self.position_size,
                'pnl': pnl,
                'fee': fee,
                'net_pnl': net_pnl,
                'capital_after': capital,
                'note': '未平仓(强制平仓)'
            })
        
        # 计算统计数据
        return self._calculate_statistics(capital)
    
    def _calculate_statistics(self, final_capital: float) -> dict:
        """计算回测统计数据"""
        if not self.trades:
            return {
                'total_trades': 0,
                'final_capital': final_capital,
                'total_return': 0,
                'total_return_pct': 0
            }
        
        trades_df = pd.DataFrame(self.trades)
        
        # 基础统计
        total_trades = len(trades_df)
        long_trades = len(trades_df[trades_df['direction'] == 'LONG'])
        short_trades = len(trades_df[trades_df['direction'] == 'SHORT'])
        
        # 盈亏统计
        winning_trades = trades_df[trades_df['net_pnl'] > 0]
        losing_trades = trades_df[trades_df['net_pnl'] < 0]
        
        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        win_rate = win_count / total_trades * 100 if total_trades > 0 else 0
        
        total_profit = winning_trades['net_pnl'].sum() if len(winning_trades) > 0 else 0
        total_loss = abs(losing_trades['net_pnl'].sum()) if len(losing_trades) > 0 else 0
        
        max_profit = trades_df['net_pnl'].max()
        max_loss = trades_df['net_pnl'].min()
        avg_profit = winning_trades['net_pnl'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['net_pnl'].mean() if len(losing_trades) > 0 else 0
        
        # 做多/做空统计
        long_pnl = trades_df[trades_df['direction'] == 'LONG']['net_pnl'].sum()
        short_pnl = trades_df[trades_df['direction'] == 'SHORT']['net_pnl'].sum()
        
        # 收益统计
        net_profit = final_capital - self.initial_capital
        total_return_pct = (final_capital - self.initial_capital) / self.initial_capital * 100
        
        # 资金曲线统计
        equity_df = pd.DataFrame(self.equity_curve)
        max_equity = equity_df['equity'].max()
        min_equity = equity_df['equity'].min()
        
        # 最大回撤
        equity_df['running_max'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['running_max'] - equity_df['equity']) / equity_df['running_max'] * 100
        max_drawdown = equity_df['drawdown'].max()
        
        return {
            'initial_capital': self.initial_capital,
            'final_capital': final_capital,
            'net_profit': net_profit,
            'total_return_pct': total_return_pct,
            'total_trades': total_trades,
            'long_trades': long_trades,
            'short_trades': short_trades,
            'win_count': win_count,
            'loss_count': loss_count,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'total_loss': total_loss,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'long_pnl': long_pnl,
            'short_pnl': short_pnl,
            'max_equity': max_equity,
            'min_equity': min_equity,
            'max_drawdown': max_drawdown,
            'profit_factor': total_profit / total_loss if total_loss > 0 else float('inf')
        }
    
    def get_trades_df(self) -> pd.DataFrame:
        """获取交易记录DataFrame"""
        if not self.trades:
            return pd.DataFrame()
        return pd.DataFrame(self.trades)
    
    def get_equity_df(self) -> pd.DataFrame:
        """获取资金曲线DataFrame"""
        if not self.equity_curve:
            return pd.DataFrame()
        return pd.DataFrame(self.equity_curve)


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, stats: dict, trades_df: pd.DataFrame, equity_df: pd.DataFrame, price_df: pd.DataFrame):
        self.stats = stats
        self.trades_df = trades_df
        self.equity_df = equity_df
        self.price_df = price_df
    
    def print_summary(self):
        """打印回测摘要"""
        print("\n" + "=" * 60)
        print("          通道突破策略回测报告")
        print("          Channel Break Out Strategy Backtest Report")
        print("=" * 60)
        
        print("\n【基本信息】")
        print(f"  策略: 5周期通道突破策略")
        print(f"  周期: 1分钟K线")
        print(f"  回测时间: {self.price_df.index[0]} 至 {self.price_df.index[-1]}")
        print(f"  K线数量: {len(self.price_df)}")
        
        print("\n【资金设置】")
        print(f"  初始资金: ${self.stats['initial_capital']:,.2f}")
        print(f"  单次开仓: 0.1 BTC")
        print(f"  手续费率: 0%")
        
        print("\n【收益统计】")
        print(f"  最终资金: ${self.stats['final_capital']:,.2f}")
        print(f"  净利润: ${self.stats['net_profit']:,.2f}")
        print(f"  收益率: {self.stats['total_return_pct']:.2f}%")
        print(f"  毛利润: ${self.stats['total_profit']:,.2f}")
        print(f"  毛亏损: ${self.stats['total_loss']:,.2f}")
        print(f"  盈亏比: {self.stats['profit_factor']:.2f}")
        
        print("\n【交易统计】")
        print(f"  总交易次数: {self.stats['total_trades']}")
        print(f"    - 做多: {self.stats['long_trades']} 笔 (盈亏: ${self.stats['long_pnl']:,.2f})")
        print(f"    - 做空: {self.stats['short_trades']} 笔 (盈亏: ${self.stats['short_pnl']:,.2f})")
        print(f"  盈利笔数: {self.stats['win_count']}")
        print(f"  亏损笔数: {self.stats['loss_count']}")
        print(f"  胜率: {self.stats['win_rate']:.2f}%")
        
        print("\n【单笔统计】")
        print(f"  最大单笔盈利: ${self.stats['max_profit']:,.2f}")
        print(f"  最大单笔亏损: ${self.stats['max_loss']:,.2f}")
        print(f"  平均盈利: ${self.stats['avg_profit']:,.2f}")
        print(f"  平均亏损: ${self.stats['avg_loss']:,.2f}")
        
        print("\n【风险统计】")
        print(f"  最高资金: ${self.stats['max_equity']:,.2f}")
        print(f"  最低资金: ${self.stats['min_equity']:,.2f}")
        print(f"  最大回撤: {self.stats['max_drawdown']:.2f}%")
        
        print("\n" + "=" * 60)
    
    def print_trades_table(self, limit: int = None):
        """打印交易明细表"""
        if self.trades_df.empty:
            print("\n无交易记录")
            return
        
        print("\n【交易明细表】")
        print("-" * 120)
        
        df = self.trades_df.copy()
        if limit:
            df = df.head(limit)
        
        # 格式化显示
        display_df = df[['trade_id', 'direction', 'entry_time', 'entry_price', 
                         'exit_time', 'exit_price', 'size', 'pnl', 'net_pnl', 'capital_after']].copy()
        
        display_df['entry_time'] = display_df['entry_time'].dt.strftime('%m-%d %H:%M')
        display_df['exit_time'] = display_df['exit_time'].dt.strftime('%m-%d %H:%M')
        display_df['entry_price'] = display_df['entry_price'].apply(lambda x: f"${x:,.2f}")
        display_df['exit_price'] = display_df['exit_price'].apply(lambda x: f"${x:,.2f}")
        display_df['pnl'] = display_df['pnl'].apply(lambda x: f"${x:,.2f}")
        display_df['net_pnl'] = display_df['net_pnl'].apply(lambda x: f"${x:,.2f}")
        display_df['capital_after'] = display_df['capital_after'].apply(lambda x: f"${x:,.2f}")
        
        display_df.columns = ['序号', '方向', '开仓时间', '开仓价', '平仓时间', '平仓价', '数量', '毛利润', '净利润', '账户余额']
        
        print(tabulate(display_df, headers='keys', tablefmt='simple', showindex=False))
        
        if limit and len(self.trades_df) > limit:
            print(f"\n... 仅显示前 {limit} 笔交易，共 {len(self.trades_df)} 笔")
    
    def plot_equity_curve(self, save_path: str = None):
        """绘制资金曲线"""
        if self.equity_df.empty:
            print("无资金曲线数据")
            return
        
        fig, axes = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [2, 1]})
        
        # 资金曲线
        ax1 = axes[0]
        ax1.plot(self.equity_df['time'], self.equity_df['equity'], 'b-', linewidth=1, label='Equity')
        ax1.axhline(y=self.stats['initial_capital'], color='gray', linestyle='--', label='Initial Capital')
        ax1.fill_between(self.equity_df['time'], self.stats['initial_capital'], 
                        self.equity_df['equity'], alpha=0.3, 
                        where=(self.equity_df['equity'] >= self.stats['initial_capital']), 
                        color='green', label='Profit')
        ax1.fill_between(self.equity_df['time'], self.stats['initial_capital'], 
                        self.equity_df['equity'], alpha=0.3, 
                        where=(self.equity_df['equity'] < self.stats['initial_capital']), 
                        color='red', label='Loss')
        
        ax1.set_title('Equity Curve (资金曲线)', fontsize=14)
        ax1.set_ylabel('Equity (USD)', fontsize=12)
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        
        # 价格走势
        ax2 = axes[1]
        ax2.plot(self.price_df.index, self.price_df['close'], 'k-', linewidth=0.5, label='Price')
        ax2.set_title('Price Chart (价格走势)', fontsize=14)
        ax2.set_ylabel('Price (USD)', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"\n资金曲线图已保存: {save_path}")
        
        plt.close()
    
    def save_trades_csv(self, path: str):
        """保存交易记录到CSV"""
        if self.trades_df.empty:
            print("无交易记录可保存")
            return
        
        self.trades_df.to_csv(path, index=False)
        print(f"交易记录已保存: {path}")
    
    def save_equity_csv(self, path: str):
        """保存资金曲线到CSV"""
        if self.equity_df.empty:
            print("无资金曲线可保存")
            return
        
        # 每小时采样一次，减少数据量
        df = self.equity_df.set_index('time')
        df_sampled = df.resample('1H').last().dropna()
        df_sampled.to_csv(path)
        print(f"资金曲线已保存: {path}")


def run_backtest(df: pd.DataFrame, strategy_mode: str, initial_capital: float, 
                 position_size: float, fee_rate: float, channel_period: int = 5) -> tuple:
    """
    运行单次回测
    
    Args:
        df: K线数据
        strategy_mode: 策略模式 'close' 或 'high_low'
        initial_capital: 初始资金
        position_size: 仓位大小
        fee_rate: 手续费率
        channel_period: 通道周期
        
    Returns:
        (stats, trades_df, equity_df)
    """
    df_copy = df.copy()
    
    # 选择策略模式
    use_high_low = (strategy_mode == 'high_low')
    strategy = ChannelBreakoutStrategy(period=channel_period, use_high_low=use_high_low)
    
    df_copy = strategy.calculate_channels(df_copy)
    df_copy = strategy.generate_signals(df_copy)
    
    # 运行回测
    backtester = Backtester(
        initial_capital=initial_capital,
        position_size=position_size,
        fee_rate=fee_rate
    )
    
    stats = backtester.run(df_copy)
    trades_df = backtester.get_trades_df()
    equity_df = backtester.get_equity_df()
    
    return stats, trades_df, equity_df, df_copy


def main():
    """主函数"""
    print("=" * 60)
    print("  通道突破策略回测系统")
    print("  Channel Break Out Strategy Backtest System")
    print("=" * 60)
    
    # 配置参数
    symbol = "BTCUSDT"  # 交易对
    interval = "1m"      # K线周期
    channel_period = 5   # 通道周期
    
    # 回测时间范围 - 2025年12月
    start_time = datetime(2025, 12, 1, 0, 0, 0)
    end_time = datetime(2025, 12, 12, 0, 0, 0)  # 到今天
    
    # 资金配置
    initial_capital = 10000  # 初始资金 $10,000
    position_size = 0.1      # 单次开仓 0.1 BTC
    fee_rate = 0.0           # 手续费率 0%
    
    print(f"\n【配置参数】")
    print(f"  交易对: {symbol}")
    print(f"  K线周期: {interval}")
    print(f"  通道周期: {channel_period}")
    print(f"  初始资金: ${initial_capital:,}")
    print(f"  单次开仓: {position_size} BTC")
    print(f"  手续费率: {fee_rate * 100}%")
    
    # 1. 获取数据
    fetcher = BinanceDataFetcher()
    df = fetcher.fetch_klines(symbol, interval, start_time, end_time)
    
    use_simulated = False
    if df.empty:
        print("\n无法从币安获取数据，使用模拟数据进行演示...")
        print("注意: 模拟数据仅用于演示回测系统功能，请使用真实数据进行实际回测")
        df = SimulatedDataGenerator.generate_btc_like_data(
            start_time, end_time, 
            interval_minutes=1,
            start_price=89000,  # 基于TradingView图表的起始价格
            volatility=0.0003
        )
        use_simulated = True
    
    print(f"\n数据范围: {df.index[0]} 至 {df.index[-1]}")
    print(f"数据条数: {len(df)}")
    
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. 运行两种模式的回测进行对比
    print("\n" + "=" * 60)
    print("运行两种信号模式进行对比...")
    print("=" * 60)
    
    # 模式1: 使用收盘价突破
    print("\n【模式1: 收盘价突破】")
    stats1, trades1, equity1, df1 = run_backtest(
        df, 'close', initial_capital, position_size, fee_rate, channel_period
    )
    
    # 模式2: 使用最高/最低价突破 (更接近TradingView)
    print("\n【模式2: 最高/最低价突破 (TradingView模式)】")
    stats2, trades2, equity2, df2 = run_backtest(
        df, 'high_low', initial_capital, position_size, fee_rate, channel_period
    )
    
    # 3. 打印对比结果
    print("\n" + "=" * 60)
    print("          策略对比结果")
    print("=" * 60)
    
    comparison_data = [
        ['指标', '收盘价突破', '最高/最低价突破'],
        ['净利润', f"${stats1['net_profit']:,.2f}", f"${stats2['net_profit']:,.2f}"],
        ['收益率', f"{stats1['total_return_pct']:.2f}%", f"{stats2['total_return_pct']:.2f}%"],
        ['总交易次数', stats1['total_trades'], stats2['total_trades']],
        ['胜率', f"{stats1['win_rate']:.2f}%", f"{stats2['win_rate']:.2f}%"],
        ['做多盈亏', f"${stats1['long_pnl']:,.2f}", f"${stats2['long_pnl']:,.2f}"],
        ['做空盈亏', f"${stats1['short_pnl']:,.2f}", f"${stats2['short_pnl']:,.2f}"],
        ['最大回撤', f"{stats1['max_drawdown']:.2f}%", f"{stats2['max_drawdown']:.2f}%"],
        ['盈亏比', f"{stats1['profit_factor']:.2f}", f"{stats2['profit_factor']:.2f}"],
        ['最大盈利', f"${stats1['max_profit']:,.2f}", f"${stats2['max_profit']:,.2f}"],
        ['最大亏损', f"${stats1['max_loss']:,.2f}", f"${stats2['max_loss']:,.2f}"],
    ]
    
    print(tabulate(comparison_data, headers='firstrow', tablefmt='grid'))
    
    # 4. 生成详细报告 (使用收盘价模式作为主要报告)
    report = ReportGenerator(stats1, trades1, equity1, df1)
    
    print("\n" + "=" * 60)
    print("          收盘价突破模式详细报告")
    print("=" * 60)
    report.print_summary()
    
    # 打印交易表（显示前50笔）
    report.print_trades_table(limit=50)
    
    # 保存文件
    report.plot_equity_curve(os.path.join(output_dir, 'equity_curve_close.png'))
    report.save_trades_csv(os.path.join(output_dir, 'trades_close.csv'))
    report.save_equity_csv(os.path.join(output_dir, 'equity_curve_close.csv'))
    
    # 保存最高/最低价模式的结果
    report2 = ReportGenerator(stats2, trades2, equity2, df2)
    report2.plot_equity_curve(os.path.join(output_dir, 'equity_curve_highlow.png'))
    report2.save_trades_csv(os.path.join(output_dir, 'trades_highlow.csv'))
    report2.save_equity_csv(os.path.join(output_dir, 'equity_curve_highlow.csv'))
    
    # 与TradingView对比
    print("\n" + "=" * 60)
    print("【与TradingView实盘对比参考】")
    print("=" * 60)
    
    # TradingView数据换算到相同仓位
    # TV: 初始100万，净利润+47713 = +4.77%
    # 如果换算到1万初始资金: 10000 * 4.77% = $477
    tv_equivalent_profit = 10000 * 0.0477
    
    print(f"""
TradingView显示 (12月1日-12月12日):
  - 初始资本: $1,000,000
  - 净利润: +$47,713 (+4.77%)
  - 做多盈利: +$24,819 (+2.48%)
  - 做空盈利: +$22,894 (+2.29%)
  - 毛利润: $121,634 (12.16%)
  - 换算至1万本金: 约 +${tv_equivalent_profit:,.2f}

本次回测结果对比:
  
  收盘价突破模式:
    - 净利润: ${stats1['net_profit']:,.2f} ({stats1['total_return_pct']:.2f}%)
    - 做多盈利: ${stats1['long_pnl']:,.2f}
    - 做空盈利: ${stats1['short_pnl']:,.2f}
    - 总交易: {stats1['total_trades']} 笔
    
  最高/最低价突破模式 (TradingView风格):
    - 净利润: ${stats2['net_profit']:,.2f} ({stats2['total_return_pct']:.2f}%)
    - 做多盈利: ${stats2['long_pnl']:,.2f}
    - 做空盈利: ${stats2['short_pnl']:,.2f}
    - 总交易: {stats2['total_trades']} 笔
  
差异分析:
  1. 数据源差异: 币安现货数据 vs TradingView数据
  2. 开仓价格差异: 回测使用K线收盘价，实盘使用突破瞬间价格
  3. 信号判断差异: TradingView可能使用实时价格判断突破
  4. 执行差异: 实盘可能有滑点和延迟
  
建议: 
  - TradingView显示的是理想化回测结果
  - 实际交易中收益通常会低于回测
  - 建议使用更保守的预期进行风险评估
""")
    
    print("\n回测完成！")
    print(f"\n输出文件:")
    print(f"  - {os.path.join(output_dir, 'trades_close.csv')} (收盘价模式交易记录)")
    print(f"  - {os.path.join(output_dir, 'trades_highlow.csv')} (最高/最低价模式交易记录)")
    print(f"  - {os.path.join(output_dir, 'equity_curve_close.png')} (收盘价模式资金曲线)")
    print(f"  - {os.path.join(output_dir, 'equity_curve_highlow.png')} (最高/最低价模式资金曲线)")


if __name__ == "__main__":
    main()
