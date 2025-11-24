# 快速开始指南

## 1. 安装依赖

```bash
npm install
```

## 2. 配置API密钥

1. 在Backpack Exchange创建API密钥: https://backpack.exchange/settings/api
2. 复制 `.env.example` 为 `.env`:
   ```bash
   cp trading-bot/.env.example trading-bot/.env
   ```
3. 编辑 `trading-bot/.env`，填入你的API密钥

## 3. 运行机器人

```bash
npm run trading-bot
```

或者:

```bash
node trading-bot/btcRsiBot.js
```

## 4. 监控日志

机器人会输出以下信息：
- 当前RSI值
- 持仓状态
- 订单执行情况
- 盈亏情况

## 5. 停止机器人

按 `Ctrl+C` 停止机器人

## 重要提示

⚠️ **使用真实资金前请务必**:
1. 在测试环境或小额资金上测试
2. 理解所有交易逻辑
3. 确保API密钥权限设置正确（只允许交易，不允许提现）
4. 建议使用进程管理器（如PM2）在生产环境运行

## 使用PM2运行（推荐）

```bash
# 安装PM2
npm install -g pm2

# 启动机器人
pm2 start trading-bot/btcRsiBot.js --name btc-rsi-bot

# 查看日志
pm2 logs btc-rsi-bot

# 停止机器人
pm2 stop btc-rsi-bot

# 重启机器人
pm2 restart btc-rsi-bot
```
