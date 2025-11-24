"""
交易机器人配置文件
"""

# 交易配置
SYMBOL = "BTC_USDT"
TIMEFRAME = "1m"  # 1分钟K线

# RSI参数
RSI_PERIOD = 14
RSI_OVERBOUGHT = 71  # RSI超过71开空
RSI_OVERSOLD = 29    # RSI低于29开多

# 初始仓位
INITIAL_POSITION_SIZE = 0.03  # BTC

# 手续费
MAKER_FEE = 0.0000  # 限价单手续费 0%
TAKER_FEE = 0.0002  # 市价单手续费 0.02%

# 加仓策略（价格逆向移动的美元数 -> 加仓数量）
SCALE_IN_LEVELS = [
    (150, 0.05),
    (250, 0.08),
    (500, 0.10),
    (800, 0.15),
    (1200, 0.20),
    (1500, 0.30)
]

# 风险管理
MIN_ORDER_INTERVAL = 20  # 订单间隔最少20秒
MAX_POSITION_SIZE = 2.0  # 最大持仓2 BTC
STOP_LOSS_USD = 1000  # 止损1000美元

# API配置（从环境变量读取）
BACKPACK_API_KEY = ""  # 在.env文件中设置
BACKPACK_SECRET_KEY = ""  # 在.env文件中设置

# 数据源配置
USE_BINANCE_PRICE = True  # True使用币安价格，False使用Backpack价格
