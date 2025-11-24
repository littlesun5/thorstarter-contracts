# BTC RSI 自动交易机器人

基于RSI指标的BTC自动交易机器人，用于Backpack.exchange交易所。

## 功能特性

### 交易策略
- ✅ RSI指标监控（14周期，每分钟更新）
- ✅ RSI > 71时开空单（0.03 BTC）
- ✅ RSI < 29时开多单（0.03 BTC）
- ✅ 智能止盈：利润覆盖手续费时自动平仓
- ✅ 止损保护：亏损达到$1000时自动止损

### 加仓策略（马丁格尔式）
当持仓被套时，价格继续逆向移动会自动加仓：

| 价格逆向移动 | 加仓数量 | 累计持仓 |
|------------|---------|---------|
| $150       | 0.05 BTC | 0.08 BTC |
| $250       | 0.08 BTC | 0.16 BTC |
| $500       | 0.10 BTC | 0.26 BTC |
| $800       | 0.15 BTC | 0.41 BTC |
| $1200      | 0.20 BTC | 0.61 BTC |
| $1500      | 0.30 BTC | 0.91 BTC |

### 风险管理
- ✅ 最大持仓限制：2 BTC
- ✅ 订单间隔：至少20秒
- ✅ 止损线：$1000
- ✅ 手续费优化：市价单0.02%，限价单0%

### 价格数据源
- 支持币安(Binance)价格数据（推荐，更稳定）
- 支持Backpack价格数据
- 可在`config.py`中配置

## 安装步骤

### 1. 安装依赖
```bash
cd trading_bot
pip install -r requirements.txt
```

### 2. 配置API密钥
复制环境变量模板：
```bash
cp .env.example .env
```

编辑`.env`文件，填入你的Backpack API密钥：
```
BACKPACK_API_KEY=your_actual_api_key
BACKPACK_SECRET_KEY=your_actual_secret_key
DRY_RUN=true
```

⚠️ **重要安全提示**：
- 不要将`.env`文件提交到git仓库
- 建议先使用模拟模式测试（DRY_RUN=true）
- API密钥应该只有交易权限，不要赋予提现权限

### 3. 获取Backpack API密钥
1. 访问 [Backpack.exchange](https://backpack.exchange/)
2. 登录账户
3. 进入API管理页面
4. 创建新的API密钥
5. 设置权限：仅需要交易权限
6. 记录API Key和Secret Key

## 使用方法

### 模拟模式（推荐先测试）
```bash
python main.py
```

默认为模拟模式，不会实际下单，可以安全测试策略逻辑。

### 真实交易模式
修改`.env`文件：
```
DRY_RUN=false
```

然后启动：
```bash
python main.py
```

⚠️ 启动时会要求输入"YES"确认，以防止误操作。

## 配置说明

在`config.py`中可以调整以下参数：

### RSI参数
```python
RSI_PERIOD = 14          # RSI周期
RSI_OVERBOUGHT = 71      # 超买阈值
RSI_OVERSOLD = 29        # 超卖阈值
```

### 仓位管理
```python
INITIAL_POSITION_SIZE = 0.03  # 初始仓位
MAX_POSITION_SIZE = 2.0       # 最大持仓
```

### 加仓级别
```python
SCALE_IN_LEVELS = [
    (150, 0.05),   # 逆向$150加仓0.05
    (250, 0.08),   # 逆向$250加仓0.08
    # ... 更多级别
]
```

### 风控参数
```python
MIN_ORDER_INTERVAL = 20   # 订单最小间隔（秒）
STOP_LOSS_USD = 1000     # 止损金额（美元）
```

## 日志文件

机器人运行时会生成`trading_bot.log`日志文件，记录所有操作：
- RSI值变化
- 开仓/平仓操作
- 加仓触发
- 盈亏情况
- 错误信息

## 监控和管理

### 查看运行日志
```bash
tail -f trading_bot.log
```

### 停止机器人
按 `Ctrl+C` 安全停止机器人。

⚠️ 如果有持仓，停止时会提醒，需要手动处理或重启机器人。

## 风险提示

⚠️ **重要风险警告**：

1. **高风险策略**：马丁格尔加仓策略在极端行情下可能导致巨额亏损
2. **测试充分**：务必在模拟模式下充分测试
3. **小额开始**：真实交易建议先用小额资金测试
4. **监控必要**：定期检查机器人运行状态和持仓情况
5. **止损重要**：确保止损设置合理，不要轻易修改
6. **网络稳定**：确保运行环境网络稳定，避免API调用失败
7. **资金管理**：不要投入超过你能承受损失的资金

## 常见问题

### Q: 如何修改交易对？
A: 在`config.py`中修改`SYMBOL`变量。

### Q: 可以同时运行多个交易对吗？
A: 需要为每个交易对启动独立的机器人实例。

### Q: 如何优化RSI参数？
A: 建议先在模拟模式下回测不同参数，找到最适合当前市场的配置。

### Q: API调用失败怎么办？
A: 检查网络连接、API密钥是否正确、Backpack服务是否正常。

### Q: 机器人会自动恢复持仓吗？
A: 不会。如果机器人重启，需要手动输入当前持仓信息或清空持仓。

## 技术架构

```
trading_bot/
├── main.py              # 启动脚本
├── trading_bot.py       # 核心交易逻辑
├── config.py            # 配置文件
├── rsi_calculator.py    # RSI计算模块
├── backpack_api.py      # Backpack API封装
├── binance_api.py       # 币安API封装（仅读取价格）
├── requirements.txt     # Python依赖
├── .env.example         # 环境变量模板
└── README.md           # 说明文档
```

## 更新日志

### v1.0.0 (2025-11-24)
- ✅ 实现基础RSI交易策略
- ✅ 实现马丁格尔加仓策略
- ✅ 实现止盈止损机制
- ✅ 实现风险管理功能
- ✅ 支持模拟模式
- ✅ 完整的日志记录

## 许可证

MIT License

## 免责声明

本软件仅供学习和研究使用。使用本软件进行实际交易的所有风险由用户自行承担。
开发者不对使用本软件造成的任何损失负责。

**加密货币交易存在极高风险，可能导致全部本金损失。请谨慎投资，理性交易。**
