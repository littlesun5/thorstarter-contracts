#!/usr/bin/env python3
"""
通道突破策略回测系统 V2 (Channel Break Out Strategy Backtest)
支持币安现货和期货数据
1分钟K线，5周期通道突破

优化版本：
- 支持期货数据
- 使用突破价格开仓（更接近TradingView）
- 详细的交易分析
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from tabulate import tabulate
import os
import sys

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class BinanceDataFetcher:
    """从币安获取K线数据（支持现货和期货）"""
    
    # 现货API端点
    SPOT_URLS = [
        "https://data-api.binance.vision/api/v3/klines",
        "https://api1.binance.com/api/v3/klines",
        "https://api2.binance.com/api/v3/klines",
    ]
    
    # 期货API端点
    FUTURES_URLS = [
        "https://fapi.binance.com/fapi/v1/klines",
        "https://fapi.binance.com/fapi/v1/klines",
    ]
    
    @staticmethod
    def fetch_klines(symbol: str, interval: str, start_time: datetime, 
                     end_time: datetime, market: str = 'spot') -> pd.DataFrame:
        """
        获取币安K线数据
        
        Args:
            symbol: 交易对，如 'BTCUSDT'
            interval: K线周期，如 '1m'
            start_time: 开始时间
            end_time: 结束时间
            market: 'spot' 或 'futures'
            
        Returns:
            DataFrame with OHLCV data
        """
        all_klines = []
        current_start = start_time
        working_url = None
        
        urls = BinanceDataFetcher.FUTURES_URLS if market == 'futures' else BinanceDataFetcher.SPOT_URLS
        
        print(f"正在从币安获取 {symbol} {interval} K线数据 ({market})...")
        print(f"时间范围: {start_time} 至 {end_time}")
        
        while current_start < end_time:
            params = {
                'symbol': symbol,
                'interval': interval,
                'startTime': int(current_start.timestamp() * 1000),
                'endTime': int(end_time.timestamp() * 1000),
                'limit': 1000
            }
            
            if working_url is None:
                for url in urls:
                    try:
                        response = requests.get(url, params=params, timeout=10)
                        if response.status_code == 200:
                            working_url = url
                            print(f"  使用数据源: {url}")
                            break
                    except:
                        continue
                        
                if working_url is None:
                    print("所有API端点均不可用")
                    break
            
            try:
                response = requests.get(working_url, params=params, timeout=30)
                response.raise_for_status()
                klines = response.json()
                
                if not klines:
                    break
                    
                all_klines.extend(klines)
                
                last_close_time = klines[-1][6]
                current_start = datetime.fromtimestamp(last_close_time / 1000) + timedelta(milliseconds=1)
                
                print(f"  已获取 {len(all_klines)} 条K线数据...", end='\r')
                
            except requests.exceptions.RequestException as e:
                print(f"\n获取数据出错: {e}")
                working_url = None
                continue
        
        print(f"\n共获取 {len(all_klines)} 条K线数据")
        
        if not all_klines:
            return pd.DataFrame()
        
        df = pd.DataFrame(all_klines, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
            'taker_buy_quote_volume', 'ignore'
        ])
        
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        df.set_index('open_time', inplace=True)
        
        return df


class ChannelBreakoutStrategy:
    """5周期通道突破策略 - 使用突破价格"""
    
    def __init__(self, period: int = 5):
        self.period = period
    
    def calculate_channels(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算通道上下轨"""
        df = df.copy()
        df['upper_channel'] = df['high'].shift(1).rolling(window=self.period).max()
        df['lower_channel'] = df['low'].shift(1).rolling(window=self.period).min()
        return df
    
    def generate_signals_with_entry_price(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号，并计算理想的入场价格
        
        TradingView方式：突破时使用通道价格作为入场价
        """
        df = df.copy()
        df['signal'] = 0
        df['entry_price'] = np.nan
        
        # 上穿上轨 -> 做多，入场价为上轨价格
        long_signal = df['high'] > df['upper_channel']
        df.loc[long_signal, 'signal'] = 1
        df.loc[long_signal, 'entry_price'] = df.loc[long_signal, 'upper_channel']
        
        # 下穿下轨 -> 做空，入场价为下轨价格
        short_signal = df['low'] < df['lower_channel']
        df.loc[short_signal, 'signal'] = -1
        df.loc[short_signal, 'entry_price'] = df.loc[short_signal, 'lower_channel']
        
        # 如果同一根K线同时触发多空信号，以收盘价方向为准
        both_signal = long_signal & short_signal
        df.loc[both_signal & (df['close'] > df['open']), 'signal'] = 1
        df.loc[both_signal & (df['close'] <= df['open']), 'signal'] = -1
        
        return df


class BacktesterV2:
    """回测引擎V2 - 支持理想入场价格"""
    
    def __init__(self, initial_capital: float = 10000, position_size: float = 0.1, 
                 fee_rate: float = 0.0, use_ideal_price: bool = True):
        self.initial_capital = initial_capital
        self.position_size = position_size
        self.fee_rate = fee_rate
        self.use_ideal_price = use_ideal_price  # 是否使用理想入场价格
        
        self.trades = []
        self.equity_curve = []
        
    def run(self, df: pd.DataFrame) -> dict:
        """运行回测"""
        capital = self.initial_capital
        position = 0
        entry_price = 0
        entry_time = None
        trade_id = 0
        
        self.trades = []
        self.equity_curve = []
        
        print(f"\n开始回测 (使用{'理想入场价' if self.use_ideal_price else '收盘价'}模式)...")
        
        for idx, row in df.iterrows():
            close_price = row['close']
            signal = row['signal']
            ideal_entry = row.get('entry_price', close_price)
            
            # 选择入场价格
            if self.use_ideal_price and not pd.isna(ideal_entry):
                trade_price = ideal_entry
            else:
                trade_price = close_price
            
            # 计算当前权益
            unrealized_pnl = 0
            if position == 1:
                unrealized_pnl = (close_price - entry_price) * self.position_size
            elif position == -1:
                unrealized_pnl = (entry_price - close_price) * self.position_size
            
            current_equity = capital + unrealized_pnl
            self.equity_curve.append({
                'time': idx,
                'equity': current_equity,
                'position': position
            })
            
            if pd.isna(signal):
                continue
            
            # 交易逻辑
            if position == 0:
                if signal == 1:
                    position = 1
                    entry_price = trade_price
                    entry_time = idx
                    trade_id += 1
                elif signal == -1:
                    position = -1
                    entry_price = trade_price
                    entry_time = idx
                    trade_id += 1
            
            elif position == 1:
                if signal == -1:
                    # 平多
                    pnl = (trade_price - entry_price) * self.position_size
                    fee = trade_price * self.position_size * self.fee_rate * 2
                    net_pnl = pnl - fee
                    capital += net_pnl
                    
                    self.trades.append({
                        'trade_id': trade_id,
                        'direction': 'LONG',
                        'entry_time': entry_time,
                        'entry_price': entry_price,
                        'exit_time': idx,
                        'exit_price': trade_price,
                        'size': self.position_size,
                        'pnl': pnl,
                        'fee': fee,
                        'net_pnl': net_pnl,
                        'capital_after': capital
                    })
                    
                    # 开空
                    position = -1
                    entry_price = trade_price
                    entry_time = idx
                    trade_id += 1
            
            elif position == -1:
                if signal == 1:
                    # 平空
                    pnl = (entry_price - trade_price) * self.position_size
                    fee = trade_price * self.position_size * self.fee_rate * 2
                    net_pnl = pnl - fee
                    capital += net_pnl
                    
                    self.trades.append({
                        'trade_id': trade_id,
                        'direction': 'SHORT',
                        'entry_time': entry_time,
                        'entry_price': entry_price,
                        'exit_time': idx,
                        'exit_price': trade_price,
                        'size': self.position_size,
                        'pnl': pnl,
                        'fee': fee,
                        'net_pnl': net_pnl,
                        'capital_after': capital
                    })
                    
                    # 开多
                    position = 1
                    entry_price = trade_price
                    entry_time = idx
                    trade_id += 1
        
        # 处理未平仓位
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
        
        total_trades = len(trades_df)
        long_trades = len(trades_df[trades_df['direction'] == 'LONG'])
        short_trades = len(trades_df[trades_df['direction'] == 'SHORT'])
        
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
        
        long_pnl = trades_df[trades_df['direction'] == 'LONG']['net_pnl'].sum()
        short_pnl = trades_df[trades_df['direction'] == 'SHORT']['net_pnl'].sum()
        
        net_profit = final_capital - self.initial_capital
        total_return_pct = (final_capital - self.initial_capital) / self.initial_capital * 100
        
        equity_df = pd.DataFrame(self.equity_curve)
        max_equity = equity_df['equity'].max()
        min_equity = equity_df['equity'].min()
        
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
        if not self.trades:
            return pd.DataFrame()
        return pd.DataFrame(self.trades)
    
    def get_equity_df(self) -> pd.DataFrame:
        if not self.equity_curve:
            return pd.DataFrame()
        return pd.DataFrame(self.equity_curve)


def print_comparison_table(results: list):
    """打印多个回测结果的对比表"""
    headers = ['模式'] + [r['name'] for r in results]
    
    rows = [
        ['净利润'] + [f"${r['stats']['net_profit']:,.2f}" for r in results],
        ['收益率'] + [f"{r['stats']['total_return_pct']:.2f}%" for r in results],
        ['总交易次数'] + [r['stats']['total_trades'] for r in results],
        ['胜率'] + [f"{r['stats']['win_rate']:.2f}%" for r in results],
        ['做多盈亏'] + [f"${r['stats']['long_pnl']:,.2f}" for r in results],
        ['做空盈亏'] + [f"${r['stats']['short_pnl']:,.2f}" for r in results],
        ['最大回撤'] + [f"{r['stats']['max_drawdown']:.2f}%" for r in results],
        ['盈亏比'] + [f"{r['stats']['profit_factor']:.2f}" for r in results],
        ['最大盈利'] + [f"${r['stats']['max_profit']:,.2f}" for r in results],
        ['最大亏损'] + [f"${r['stats']['max_loss']:,.2f}" for r in results],
    ]
    
    print(tabulate(rows, headers=headers, tablefmt='grid'))


def save_results(stats, trades_df, equity_df, df, output_dir, suffix):
    """保存回测结果"""
    # 保存交易记录
    if not trades_df.empty:
        trades_df.to_csv(os.path.join(output_dir, f'trades_{suffix}.csv'), index=False)
        print(f"  交易记录已保存: trades_{suffix}.csv")
    
    # 保存资金曲线
    if not equity_df.empty:
        df_sampled = equity_df.set_index('time').resample('1h').last().dropna()
        df_sampled.to_csv(os.path.join(output_dir, f'equity_{suffix}.csv'))
        print(f"  资金曲线已保存: equity_{suffix}.csv")


def main():
    """主函数"""
    print("=" * 70)
    print("  通道突破策略回测系统 V2")
    print("  Channel Break Out Strategy Backtest System V2")
    print("  支持现货/期货数据 + 理想入场价格模式")
    print("=" * 70)
    
    # 配置参数
    symbol = "BTCUSDT"
    interval = "1m"
    channel_period = 5
    
    # 回测时间范围
    start_time = datetime(2025, 12, 1, 0, 0, 0)
    end_time = datetime(2025, 12, 12, 0, 0, 0)
    
    # 资金配置
    initial_capital = 10000
    position_size = 0.1
    fee_rate = 0.0
    
    print(f"\n【配置参数】")
    print(f"  交易对: {symbol}")
    print(f"  K线周期: {interval}")
    print(f"  通道周期: {channel_period}")
    print(f"  初始资金: ${initial_capital:,}")
    print(f"  单次开仓: {position_size} BTC")
    print(f"  手续费率: {fee_rate * 100}%")
    
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 获取现货数据
    print("\n" + "=" * 70)
    print("获取数据...")
    print("=" * 70)
    
    fetcher = BinanceDataFetcher()
    
    # 尝试获取现货数据
    df_spot = fetcher.fetch_klines(symbol, interval, start_time, end_time, market='spot')
    
    # 尝试获取期货数据
    df_futures = fetcher.fetch_klines(symbol, interval, start_time, end_time, market='futures')
    
    if df_spot.empty and df_futures.empty:
        print("无法获取数据，请检查网络连接")
        return
    
    # 运行多种模式的回测
    results = []
    strategy = ChannelBreakoutStrategy(period=channel_period)
    
    # 模式1: 现货 + 收盘价
    if not df_spot.empty:
        print("\n【模式1: 现货数据 + 收盘价入场】")
        df = strategy.calculate_channels(df_spot.copy())
        df = strategy.generate_signals_with_entry_price(df)
        
        backtester = BacktesterV2(initial_capital, position_size, fee_rate, use_ideal_price=False)
        stats = backtester.run(df)
        
        results.append({
            'name': '现货+收盘价',
            'stats': stats,
            'trades': backtester.get_trades_df(),
            'equity': backtester.get_equity_df()
        })
        save_results(stats, backtester.get_trades_df(), backtester.get_equity_df(), 
                    df, output_dir, 'spot_close')
    
    # 模式2: 现货 + 理想入场价
    if not df_spot.empty:
        print("\n【模式2: 现货数据 + 理想入场价 (TradingView风格)】")
        df = strategy.calculate_channels(df_spot.copy())
        df = strategy.generate_signals_with_entry_price(df)
        
        backtester = BacktesterV2(initial_capital, position_size, fee_rate, use_ideal_price=True)
        stats = backtester.run(df)
        
        results.append({
            'name': '现货+理想价',
            'stats': stats,
            'trades': backtester.get_trades_df(),
            'equity': backtester.get_equity_df()
        })
        save_results(stats, backtester.get_trades_df(), backtester.get_equity_df(),
                    df, output_dir, 'spot_ideal')
    
    # 模式3: 期货 + 收盘价
    if not df_futures.empty:
        print("\n【模式3: 期货数据 + 收盘价入场】")
        df = strategy.calculate_channels(df_futures.copy())
        df = strategy.generate_signals_with_entry_price(df)
        
        backtester = BacktesterV2(initial_capital, position_size, fee_rate, use_ideal_price=False)
        stats = backtester.run(df)
        
        results.append({
            'name': '期货+收盘价',
            'stats': stats,
            'trades': backtester.get_trades_df(),
            'equity': backtester.get_equity_df()
        })
        save_results(stats, backtester.get_trades_df(), backtester.get_equity_df(),
                    df, output_dir, 'futures_close')
    
    # 模式4: 期货 + 理想入场价
    if not df_futures.empty:
        print("\n【模式4: 期货数据 + 理想入场价 (TradingView风格)】")
        df = strategy.calculate_channels(df_futures.copy())
        df = strategy.generate_signals_with_entry_price(df)
        
        backtester = BacktesterV2(initial_capital, position_size, fee_rate, use_ideal_price=True)
        stats = backtester.run(df)
        
        results.append({
            'name': '期货+理想价',
            'stats': stats,
            'trades': backtester.get_trades_df(),
            'equity': backtester.get_equity_df()
        })
        save_results(stats, backtester.get_trades_df(), backtester.get_equity_df(),
                    df, output_dir, 'futures_ideal')
    
    # 打印对比结果
    print("\n" + "=" * 70)
    print("          回测结果对比")
    print("=" * 70 + "\n")
    
    print_comparison_table(results)
    
    # 打印交易明细 (使用第一个有数据的结果)
    if results:
        best_result = results[0]
        trades_df = best_result['trades']
        
        if not trades_df.empty:
            print(f"\n\n【{best_result['name']} 交易明细 (前30笔)】")
            print("-" * 120)
            
            display_df = trades_df.head(30).copy()
            display_df['entry_time'] = pd.to_datetime(display_df['entry_time']).dt.strftime('%m-%d %H:%M')
            display_df['exit_time'] = pd.to_datetime(display_df['exit_time']).dt.strftime('%m-%d %H:%M')
            display_df['entry_price'] = display_df['entry_price'].apply(lambda x: f"${x:,.2f}")
            display_df['exit_price'] = display_df['exit_price'].apply(lambda x: f"${x:,.2f}")
            display_df['net_pnl'] = display_df['net_pnl'].apply(lambda x: f"${x:,.2f}")
            display_df['capital_after'] = display_df['capital_after'].apply(lambda x: f"${x:,.2f}")
            
            display_cols = display_df[['trade_id', 'direction', 'entry_time', 'entry_price', 
                                      'exit_time', 'exit_price', 'net_pnl', 'capital_after']]
            display_cols.columns = ['序号', '方向', '开仓时间', '开仓价', '平仓时间', '平仓价', '净利润', '账户余额']
            
            print(tabulate(display_cols, headers='keys', tablefmt='simple', showindex=False))
            
            if len(trades_df) > 30:
                print(f"\n... 共 {len(trades_df)} 笔交易")
    
    # 与TradingView对比
    print("\n" + "=" * 70)
    print("【与TradingView实盘对比分析】")
    print("=" * 70)
    
    print("""
TradingView显示 (12月1日-12月12日):
  - 初始资本: $1,000,000
  - 净利润: +$47,713 (+4.77%)
  - 做多盈利: +$24,819 (+2.48%)  
  - 做空盈利: +$22,894 (+2.29%)
  - 毛利润: $121,634 (12.16%)
  
差异分析:
  
  1. 数据源差异:
     - TradingView可能使用不同的数据提供商
     - 币安现货vs期货价格可能有差异
     
  2. 入场价格差异:
     - TradingView回测使用的是理论最优价格（突破瞬间价格）
     - 实际交易中很难获得这个价格
     
  3. 信号判断时机:
     - TradingView可能在K线内部就触发信号
     - 本回测基于K线收盘后判断
     
  4. 仓位计算差异:
     - TradingView可能使用百分比仓位
     - 本回测使用固定仓位 (0.1 BTC)

建议:
  - TradingView显示的是理想化回测结果
  - 实际交易应预期收益低于回测20-50%
  - 建议先小仓位实盘验证再放大资金
""")
    
    print("\n回测完成！")
    print(f"\n所有结果已保存到: {output_dir}/")


if __name__ == "__main__":
    main()
