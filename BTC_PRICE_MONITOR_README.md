# BTC价差监控工具

这是一个用于监控 Backpack Exchange 和 Lighter Exchange 之间 BTC 实时价差的工具。当价差超过设定阈值时会弹窗提醒。

## 功能特点

- 🔄 实时监控两个交易所的BTC价格
- 📊 计算并显示价差和百分比
- 🚨 价差超过阈值时弹窗提醒
- ⚙️ 可配置的监控间隔和阈值
- 🔔 提醒冷却机制，避免频繁通知

## 安装依赖

```bash
npm install
```

## 配置

编辑 `scripts/btcPriceMonitor.config.js` 文件来配置：

### 基本配置

- `checkInterval`: 监控间隔（毫秒），默认5000（5秒）
- `priceDiffThresholdHigh`: 价差上限阈值（美元），默认80
- `priceDiffThresholdLow`: 价差下限阈值（美元），默认10

### API配置

根据实际API文档调整以下配置：

#### Backpack Exchange
- `baseUrl`: API基础URL
- `tickerEndpoint`: 获取ticker的端点路径
- `symbol`: 交易对符号（如 `BTC_USDC` 或 `BTC-USDC`）

#### Lighter Exchange
- `baseUrl`: API基础URL
- `tickerEndpoint`: 获取ticker的端点路径
- `symbol`: 交易对符号

### API密钥（如果需要）

如果API需要认证，可以通过环境变量设置：

```bash
export BACKPACK_API_KEY=your_api_key
export BACKPACK_API_SECRET=your_api_secret
export LIGHTER_API_KEY=your_api_key
export LIGHTER_API_SECRET=your_api_secret
```

或者在配置文件中直接设置（不推荐，安全性较低）。

## 使用方法

### 启动监控

```bash
node scripts/btcPriceMonitor.js
```

或者使用npm脚本：

```bash
npm run monitor:btc
```

### 输出示例

```
🚀 BTC价差监控工具启动
📊 监控间隔: 5秒
⚠️  价差阈值: > $80 或 < $10
🔔 提醒冷却时间: 60秒

[14:30:15] Backpack: $50000.00 | Lighter: $50050.00 | 价差: $50.00 (0.10%)
[14:30:20] Backpack: $50000.00 | Lighter: $50050.00 | 价差: $50.00 (0.10%)
```

### 提醒触发

当价差超过阈值时，会：
1. 在控制台显示警告信息
2. 弹出系统通知（桌面弹窗）
3. 播放提示音（如果启用）

## API文档参考

- Backpack Exchange: https://docs.backpack.exchange/
- Lighter Exchange: https://apidocs.lighter.xyz/docs/get-started-for-programmers-1#/

## 故障排除

### 无法获取价格数据

1. **检查API端点**: 确认 `btcPriceMonitor.config.js` 中的API端点是否正确
2. **检查交易对符号**: 确认交易对符号格式是否正确（`BTC_USDC` vs `BTC-USDC`）
3. **查看错误日志**: 脚本会输出详细的错误信息，包括API响应数据
4. **检查网络连接**: 确保可以访问API服务器

### 价格解析失败

如果看到"无法解析价格数据"错误：
1. 查看控制台输出的API响应数据
2. 根据实际API响应格式，修改 `getBackpackPrice()` 或 `getLighterPrice()` 函数中的价格解析逻辑
3. 常见价格字段名：`last`, `price`, `close`, `lastPrice`, `markPrice`

### 弹窗不显示

- **Linux**: 确保已安装 `libnotify-bin` 或类似的通知系统
  ```bash
  sudo apt-get install libnotify-bin  # Ubuntu/Debian
  ```
- **macOS**: 确保系统通知权限已开启
- **Windows**: 应该自动支持

## 自定义配置示例

### 修改监控间隔

```javascript
// btcPriceMonitor.config.js
checkInterval: 10000, // 改为10秒
```

### 修改阈值

```javascript
// btcPriceMonitor.config.js
priceDiffThresholdHigh: 100, // 改为100美元
priceDiffThresholdLow: 5,    // 改为5美元
```

### 禁用声音

```javascript
// btcPriceMonitor.config.js
alert: {
  sound: false,
  // ...
}
```

## 注意事项

- 该工具会持续运行，使用 `Ctrl+C` 停止
- 建议在后台运行或使用进程管理工具（如 `pm2`）
- API可能有速率限制，请根据实际情况调整监控间隔
- 首次使用时需要根据实际API响应格式调整代码

## 后台运行示例

使用 `nohup`:

```bash
nohup node scripts/btcPriceMonitor.js > monitor.log 2>&1 &
```

使用 `pm2`:

```bash
npm install -g pm2
pm2 start scripts/btcPriceMonitor.js --name btc-monitor
pm2 logs btc-monitor
```
