"""
RSI交易机器人主逻辑
"""
import time
import logging
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass

from config import *
from rsi_calculator import RSICalculator
from backpack_api import BackpackAPI
from binance_api import BinanceAPI

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Position:
    """持仓信息"""
    side: str  # "LONG" or "SHORT"
    entries: List[Dict]  # 每次开仓的记录 [{"price": float, "quantity": float, "timestamp": int}]
    total_quantity: float
    avg_entry_price: float
    unrealized_pnl: float
    last_scale_in_level: int  # 上次加仓的级别索引，-1表示只有初始仓位
    
    def add_entry(self, price: float, quantity: float):
        """添加一笔开仓记录"""
        self.entries.append({
            "price": price,
            "quantity": quantity,
            "timestamp": int(time.time())
        })
        # 重新计算平均成本和总量
        total_cost = sum(e["price"] * e["quantity"] for e in self.entries)
        self.total_quantity = sum(e["quantity"] for e in self.entries)
        self.avg_entry_price = total_cost / self.total_quantity if self.total_quantity > 0 else 0
    
    def calculate_pnl(self, current_price: float) -> float:
        """计算当前盈亏（美元）"""
        if self.side == "LONG":
            self.unrealized_pnl = (current_price - self.avg_entry_price) * self.total_quantity
        else:  # SHORT
            self.unrealized_pnl = (self.avg_entry_price - current_price) * self.total_quantity
        return self.unrealized_pnl
    
    def get_price_move_from_entry(self, current_price: float) -> float:
        """计算价格相对于开仓价的移动（美元）"""
        return abs(current_price - self.avg_entry_price) * self.total_quantity


class TradingBot:
    """RSI交易机器人"""
    
    def __init__(self, api_key: str, secret_key: str, dry_run: bool = False):
        """
        初始化交易机器人
        
        Args:
            api_key: Backpack API密钥
            secret_key: Backpack Secret密钥
            dry_run: 是否为模拟模式（不实际下单）
        """
        self.backpack = BackpackAPI(api_key, secret_key)
        self.binance = BinanceAPI()
        self.rsi_calculator = RSICalculator(RSI_PERIOD)
        self.dry_run = dry_run
        
        # 持仓信息
        self.position: Optional[Position] = None
        
        # 最后一次下单时间
        self.last_order_time = 0
        
        # 运行状态
        self.running = False
        
        logger.info(f"交易机器人初始化完成 (模拟模式: {dry_run})")
    
    def _get_current_price(self) -> Optional[float]:
        """获取当前BTC价格"""
        try:
            if USE_BINANCE_PRICE:
                # 使用币安价格
                price = self.binance.get_ticker_price("BTCUSDT")
            else:
                # 使用Backpack价格
                ticker = self.backpack.get_ticker(SYMBOL)
                if ticker:
                    price = float(ticker.get("lastPrice", 0))
                else:
                    price = None
            
            if price:
                logger.debug(f"当前价格: ${price:.2f}")
            return price
        except Exception as e:
            logger.error(f"获取价格失败: {e}")
            return None
    
    def _get_klines(self, limit: int = 100) -> Optional[List]:
        """获取K线数据"""
        try:
            if USE_BINANCE_PRICE:
                klines = self.binance.get_klines("BTCUSDT", TIMEFRAME, limit)
            else:
                klines = self.backpack.get_klines(SYMBOL, TIMEFRAME, limit)
            return klines
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            return None
    
    def _update_rsi(self) -> Optional[float]:
        """更新并返回当前RSI值"""
        try:
            klines = self._get_klines(RSI_PERIOD + 50)
            if not klines:
                return None
            
            # 提取收盘价
            if USE_BINANCE_PRICE:
                # 币安K线格式: [open_time, open, high, low, close, volume, ...]
                close_prices = [float(k[4]) for k in klines]
            else:
                # Backpack K线格式可能不同，需要根据实际调整
                close_prices = [float(k.get("close", 0)) for k in klines]
            
            # 计算RSI
            rsi = self.rsi_calculator.calculate_rsi(close_prices)
            if rsi:
                logger.info(f"当前RSI: {rsi:.2f}")
            return rsi
        except Exception as e:
            logger.error(f"更新RSI失败: {e}")
            return None
    
    def _can_place_order(self) -> bool:
        """检查是否可以下单（20秒间隔限制）"""
        current_time = time.time()
        if current_time - self.last_order_time < MIN_ORDER_INTERVAL:
            logger.info(f"订单间隔不足，需等待 {MIN_ORDER_INTERVAL - (current_time - self.last_order_time):.1f} 秒")
            return False
        return True
    
    def _place_market_order(self, side: str, quantity: float) -> bool:
        """
        下市价单
        
        Args:
            side: "Buy" or "Sell"
            quantity: 数量
            
        Returns:
            是否成功
        """
        if not self._can_place_order():
            return False
        
        if self.dry_run:
            logger.info(f"[模拟] 市价{side}单: {quantity} BTC")
            self.last_order_time = time.time()
            return True
        
        try:
            result = self.backpack.create_order(
                symbol=SYMBOL,
                side=side,
                order_type="Market",
                quantity=quantity
            )
            
            if result:
                logger.info(f"市价{side}单成功: {quantity} BTC, 订单ID: {result.get('orderId')}")
                self.last_order_time = time.time()
                return True
            else:
                logger.error(f"市价{side}单失败")
                return False
        except Exception as e:
            logger.error(f"下单异常: {e}")
            return False
    
    def _open_position(self, side: str, quantity: float, current_price: float) -> bool:
        """
        开仓
        
        Args:
            side: "LONG" or "SHORT"
            quantity: 数量
            current_price: 当前价格
            
        Returns:
            是否成功
        """
        # 检查持仓限制
        if self.position and self.position.total_quantity + quantity > MAX_POSITION_SIZE:
            logger.warning(f"持仓将超过最大限制 {MAX_POSITION_SIZE} BTC，拒绝开仓")
            return False
        
        # 确定Backpack的买卖方向
        backpack_side = "Buy" if side == "LONG" else "Sell"
        
        # 下单
        if self._place_market_order(backpack_side, quantity):
            # 如果是新仓位
            if not self.position:
                self.position = Position(
                    side=side,
                    entries=[],
                    total_quantity=0,
                    avg_entry_price=0,
                    unrealized_pnl=0,
                    last_scale_in_level=-1
                )
            
            # 添加开仓记录
            self.position.add_entry(current_price, quantity)
            logger.info(f"开仓成功: {side} {quantity} BTC @ ${current_price:.2f}, "
                       f"总持仓: {self.position.total_quantity} BTC, "
                       f"平均成本: ${self.position.avg_entry_price:.2f}")
            return True
        
        return False
    
    def _close_position(self, reason: str = "") -> bool:
        """
        平仓
        
        Args:
            reason: 平仓原因
            
        Returns:
            是否成功
        """
        if not self.position:
            return False
        
        # 确定平仓方向（与持仓方向相反）
        backpack_side = "Sell" if self.position.side == "LONG" else "Buy"
        
        # 下单平仓
        if self._place_market_order(backpack_side, self.position.total_quantity):
            logger.info(f"平仓成功: {reason}, 盈亏: ${self.position.unrealized_pnl:.2f}")
            self.position = None
            return True
        
        return False
    
    def _check_scale_in(self, current_price: float):
        """检查是否需要加仓"""
        if not self.position:
            return
        
        # 计算价格移动
        price_diff = current_price - self.position.avg_entry_price
        
        # 判断是否逆向移动
        is_adverse_move = False
        if self.position.side == "LONG" and price_diff < 0:
            is_adverse_move = True
            move_amount = abs(price_diff)
        elif self.position.side == "SHORT" and price_diff > 0:
            is_adverse_move = True
            move_amount = abs(price_diff)
        else:
            return  # 价格朝有利方向移动，不加仓
        
        # 检查每个加仓级别
        for i, (threshold, quantity) in enumerate(SCALE_IN_LEVELS):
            # 如果已经加过这个级别，跳过
            if i <= self.position.last_scale_in_level:
                continue
            
            # 检查是否达到加仓阈值
            if move_amount >= threshold:
                # 检查持仓限制
                if self.position.total_quantity + quantity > MAX_POSITION_SIZE:
                    logger.warning(f"加仓将超过最大持仓限制 {MAX_POSITION_SIZE} BTC")
                    continue
                
                # 执行加仓
                logger.info(f"触发加仓级别 {i+1}: 价格逆向移动 ${move_amount:.2f}, 加仓 {quantity} BTC")
                if self._open_position(self.position.side, quantity, current_price):
                    self.position.last_scale_in_level = i
                break
    
    def _check_take_profit(self, current_price: float) -> bool:
        """
        检查是否满足止盈条件
        
        Returns:
            是否应该止盈
        """
        if not self.position:
            return False
        
        # 计算当前盈亏
        pnl = self.position.calculate_pnl(current_price)
        
        # 计算手续费（市价单入场和出场）
        entry_fee = self.position.avg_entry_price * self.position.total_quantity * TAKER_FEE
        exit_fee = current_price * self.position.total_quantity * TAKER_FEE
        total_fee = entry_fee + exit_fee
        
        # 判断是否覆盖手续费
        if pnl > total_fee:
            logger.info(f"满足止盈条件: 盈亏=${pnl:.2f}, 手续费=${total_fee:.2f}, 净利润=${pnl-total_fee:.2f}")
            return True
        
        return False
    
    def _check_stop_loss(self, current_price: float) -> bool:
        """
        检查是否触发止损
        
        Returns:
            是否应该止损
        """
        if not self.position:
            return False
        
        # 计算当前盈亏
        pnl = self.position.calculate_pnl(current_price)
        
        # 判断是否达到止损线
        if pnl <= -STOP_LOSS_USD:
            logger.warning(f"触发止损: 亏损 ${abs(pnl):.2f} >= ${STOP_LOSS_USD}")
            return True
        
        return False
    
    def _check_entry_signals(self, rsi: float, current_price: float):
        """检查入场信号"""
        # 如果已有持仓，不开新仓
        if self.position:
            return
        
        # RSI超买，开空
        if rsi > RSI_OVERBOUGHT:
            logger.info(f"RSI超买信号: {rsi:.2f} > {RSI_OVERBOUGHT}, 开空单")
            self._open_position("SHORT", INITIAL_POSITION_SIZE, current_price)
        
        # RSI超卖，开多
        elif rsi < RSI_OVERSOLD:
            logger.info(f"RSI超卖信号: {rsi:.2f} < {RSI_OVERSOLD}, 开多单")
            self._open_position("LONG", INITIAL_POSITION_SIZE, current_price)
    
    def run_strategy(self):
        """运行一次策略逻辑"""
        try:
            # 获取当前价格
            current_price = self._get_current_price()
            if not current_price:
                logger.warning("无法获取当前价格，跳过此次循环")
                return
            
            # 更新RSI
            rsi = self._update_rsi()
            if not rsi:
                logger.warning("无法计算RSI，跳过此次循环")
                return
            
            # 如果有持仓，先检查止损和止盈
            if self.position:
                self.position.calculate_pnl(current_price)
                logger.info(f"当前持仓: {self.position.side} {self.position.total_quantity} BTC, "
                           f"均价: ${self.position.avg_entry_price:.2f}, "
                           f"盈亏: ${self.position.unrealized_pnl:.2f}")
                
                # 检查止损
                if self._check_stop_loss(current_price):
                    self._close_position("止损")
                    return
                
                # 检查止盈
                if self._check_take_profit(current_price):
                    self._close_position("止盈")
                    return
                
                # 检查加仓
                self._check_scale_in(current_price)
            
            # 检查入场信号
            else:
                self._check_entry_signals(rsi, current_price)
        
        except Exception as e:
            logger.error(f"策略运行异常: {e}", exc_info=True)
    
    def start(self, interval: int = 60):
        """
        启动交易机器人
        
        Args:
            interval: 检查间隔（秒），默认60秒
        """
        logger.info("=" * 50)
        logger.info("交易机器人启动")
        logger.info(f"交易对: {SYMBOL}")
        logger.info(f"RSI周期: {RSI_PERIOD}, 超买: {RSI_OVERBOUGHT}, 超卖: {RSI_OVERSOLD}")
        logger.info(f"初始仓位: {INITIAL_POSITION_SIZE} BTC")
        logger.info(f"最大持仓: {MAX_POSITION_SIZE} BTC")
        logger.info(f"止损: ${STOP_LOSS_USD}")
        logger.info(f"模拟模式: {self.dry_run}")
        logger.info("=" * 50)
        
        self.running = True
        
        while self.running:
            try:
                self.run_strategy()
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("收到停止信号")
                self.stop()
                break
            except Exception as e:
                logger.error(f"运行异常: {e}", exc_info=True)
                time.sleep(interval)
    
    def stop(self):
        """停止交易机器人"""
        logger.info("正在停止交易机器人...")
        self.running = False
        
        # 如果有持仓，提醒用户
        if self.position:
            logger.warning(f"当前仍有持仓: {self.position.side} {self.position.total_quantity} BTC")
            logger.warning("请手动处理持仓或重启机器人")
        
        logger.info("交易机器人已停止")
