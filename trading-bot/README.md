# BTC RSI Trading Bot for Backpack Exchange

这是一个基于RSI指标的BTC自动交易机器人，用于在Backpack交易所进行交易。

## 功能特性

- **RSI监控**: 每分钟获取BTC的RSI数据（使用Backpack或Binance价格）
- **自动开仓**: 
  - RSI > 71时开0.03 BTC空单
  - RSI < 29时开0.03 BTC多单
- **自动平仓**: 当利润可以覆盖手续费时自动平仓
- **加仓策略**: 当持仓亏损且RSI继续向不利方向移动时，按以下规则加仓：
  - 亏损$150: 加仓0.05 BTC
  - 亏损$250: 加仓0.08 BTC
  - 亏损$500: 加仓0.10 BTC
  - 亏损$800: 加仓0.15 BTC
  - 亏损$1200: 加仓0.20 BTC
  - 亏损$1500: 加仓0.30 BTC
- **风险控制**:
  - 最大持仓: 2 BTC
  - 止损: $1000亏损时市价平仓
  - 订单间隔: 至少20秒
- **手续费**: 市价单0.02%，限价单0%

## 安装

1. 安装依赖:
```bash
npm install
```

2. 配置环境变量:
```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的Backpack API密钥:
```
BACKPACK_API_KEY=your_api_key_here
BACKPACK_API_SECRET=your_api_secret_here
```

## 使用方法

运行机器人:
```bash
node trading-bot/btcRsiBot.js
```

机器人会：
1. 每分钟检查一次RSI
2. 根据RSI值决定是否开仓
3. 监控持仓，在满足条件时平仓或加仓
4. 执行止损保护

## 注意事项

⚠️ **重要警告**:
- 这是一个自动化交易机器人，使用真实资金交易有风险
- 建议先在测试环境或小额资金上测试
- 确保你理解所有交易逻辑和风险
- 机器人会持续运行，请确保服务器稳定
- 建议使用进程管理器（如PM2）来运行机器人

## 配置说明

可以在 `btcRsiBot.js` 中修改以下参数：

- `initialOrderSize`: 初始订单大小（默认0.03 BTC）
- `maxPosition`: 最大持仓（默认2.0 BTC）
- `stopLossUSD`: 止损金额（默认$1000）
- `rsiShortThreshold`: RSI做空阈值（默认71）
- `rsiLongThreshold`: RSI做多阈值（默认29）
- `minOrderInterval`: 最小订单间隔（默认20000毫秒）

## API文档

Backpack Exchange API文档: https://docs.backpack.exchange/

## 许可证

MIT
