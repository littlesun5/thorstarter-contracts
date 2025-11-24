# BTC RSI 交易机器人使用说明

## 📦 项目位置
交易机器人代码位于：`/workspace/trading_bot/`

## 🎯 功能特性

根据你的需求，我已经创建了一个完整的自动交易机器人，实现了以下功能：

### ✅ 核心交易策略
- **RSI信号检测**：
  - RSI > 71 时自动开空单（0.03 BTC）
  - RSI < 29 时自动开多单（0.03 BTC）
  - 使用14周期RSI，每分钟更新

- **智能止盈**：
  - 当利润可以覆盖手续费时自动平仓
  - 考虑市价单0.02%和限价单0%的手续费

- **马丁格尔加仓策略**：
  - $150 → 加仓 0.05 BTC
  - $250 → 加仓 0.08 BTC
  - $500 → 加仓 0.10 BTC
  - $800 → 加仓 0.15 BTC
  - $1200 → 加仓 0.20 BTC
  - $1500 → 加仓 0.30 BTC

- **风险控制**：
  - 最大持仓：2 BTC
  - 订单间隔：≥20秒
  - 止损线：$1000

### 📊 数据源
- 支持币安(Binance)价格数据（推荐）
- 支持Backpack交易所价格数据
- 可在配置文件中切换

## 🚀 快速开始

### 1. 安装依赖
```bash
cd /workspace/trading_bot
pip install -r requirements.txt
```

### 2. 配置API密钥
```bash
cp .env.example .env
# 编辑.env文件，填入你的Backpack API密钥
```

### 3. 测试连接
```bash
python test_connection.py
```

### 4. 启动机器人（模拟模式）
```bash
python main.py
```

## 📁 文件结构

```
trading_bot/
├── main.py              # 启动脚本
├── trading_bot.py       # 核心交易逻辑（15KB+代码）
├── config.py            # 所有配置参数
├── rsi_calculator.py    # RSI指标计算
├── backpack_api.py      # Backpack API封装
├── binance_api.py       # 币安API封装
├── test_connection.py   # 连接测试工具
├── requirements.txt     # Python依赖
├── .env.example         # 配置模板
├── .gitignore          # Git忽略文件
├── README.md           # 完整文档
└── QUICKSTART.md       # 快速指南
```

## ⚙️ 配置说明

在 `config.py` 中可以调整：

```python
# RSI参数
RSI_PERIOD = 14          # RSI周期
RSI_OVERBOUGHT = 71      # 超买阈值
RSI_OVERSOLD = 29        # 超卖阈值

# 仓位
INITIAL_POSITION_SIZE = 0.03  # 初始仓位
MAX_POSITION_SIZE = 2.0       # 最大持仓

# 风控
STOP_LOSS_USD = 1000     # 止损金额
MIN_ORDER_INTERVAL = 20   # 订单间隔

# 加仓级别（可自定义）
SCALE_IN_LEVELS = [...]
```

## 🔒 安全提示

⚠️ **重要**：
1. **先用模拟模式测试**（DRY_RUN=true）
2. API密钥**只授予交易权限**，不要给提现权限
3. `.env`文件已在`.gitignore`中，不会提交到Git
4. 建议从小资金开始测试真实交易
5. 定期检查机器人运行状态

## 📊 监控

### 查看实时日志
```bash
tail -f /workspace/trading_bot/trading_bot.log
```

日志记录内容：
- RSI值变化
- 开仓/平仓操作
- 加仓触发
- 盈亏统计
- 错误信息

### 停止机器人
```bash
按 Ctrl+C
```

## ⚠️ 风险警示

**高风险警告**：
- 马丁格尔策略在极端行情下风险极高
- 可能导致快速且巨大的亏损
- 强烈建议充分测试后再用真实资金
- 不要投入超过可承受损失的资金

## 🛠️ 高级功能

### 自定义交易对
修改 `config.py` 中的 `SYMBOL` 变量

### 多交易对运行
为每个交易对启动独立的机器人实例

### 参数优化
在模拟模式下测试不同的RSI参数组合

## 📞 技术支持

查看详细文档：
- 完整说明：`/workspace/trading_bot/README.md`
- 快速指南：`/workspace/trading_bot/QUICKSTART.md`

## ✨ 已实现功能清单

- ✅ RSI指标计算和监控
- ✅ 自动开仓（RSI信号触发）
- ✅ 智能止盈（覆盖手续费）
- ✅ 智能止损（$1000）
- ✅ 马丁格尔加仓（6个级别）
- ✅ 风险控制（持仓限制、订单间隔）
- ✅ 完整日志记录
- ✅ 模拟模式
- ✅ 连接测试工具
- ✅ 双数据源支持（币安/Backpack）
- ✅ 详细文档和注释

机器人已准备就绪！🎉
