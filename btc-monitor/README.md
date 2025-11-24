# BTC 价差监控器

一个实时监控 Backpack Exchange 和 Lighter 交易所 BTC 价格差异的工具。

## 功能特点

- 🔄 **实时价格监控** - 自动获取两个交易所的BTC最新价格
- 📊 **价差计算** - 实时计算并显示价格差异
- 🚨 **智能报警** - 当价差超出设定阈值时自动弹窗提醒
- 📈 **图表可视化** - 实时显示价差变化趋势图
- 📝 **历史记录** - 保存报警历史记录
- ⚙️ **自定义设置** - 可调整报警阈值和刷新间隔

## 安装与运行

### 方法一：使用代理服务器（推荐）

由于浏览器的CORS限制，推荐使用代理服务器运行：

1. 进入项目目录：
   ```bash
   cd /workspace/btc-monitor
   ```

2. 安装依赖：
   ```bash
   npm install
   ```

3. 启动代理服务器：
   ```bash
   npm start
   ```

4. 在浏览器中访问：
   ```
   http://localhost:3000
   ```

### 方法二：直接打开HTML文件

如果API支持CORS，可以直接在浏览器中打开 `index.html` 文件。

## 使用说明

### 设置报警阈值

- **最小价差阈值**：当价差小于此值时触发报警（默认 $10）
- **最大价差阈值**：当价差大于此值时触发报警（默认 $80）

### 控制面板

- **开始监控**：点击开始按钮启动实时监控
- **停止监控**：点击停止按钮暂停监控
- **刷新间隔**：设置价格更新频率（1-60秒）

### 报警方式

当价差超出阈值范围时，系统会通过以下方式提醒：

1. 🔔 浏览器弹窗通知
2. 📢 页面内弹窗提示
3. 🔊 声音提醒
4. 📋 记录到报警历史

## 技术栈

- **前端**：HTML5 + CSS3 + JavaScript
- **图表库**：Chart.js
- **后端代理**：Node.js + Express
- **HTTP客户端**：Axios

## API说明

### Backpack Exchange
- API文档：https://docs.backpack.exchange/
- 端点：`/api/v1/ticker?symbol=BTC_USDC`

### Lighter
- API文档：https://apidocs.lighter.xyz/
- 端点：`/v1/markets`

## 注意事项

1. 首次使用时需要授权浏览器通知权限
2. 确保网络连接稳定，以获取实时价格
3. 建议使用Chrome或Firefox等现代浏览器
4. 如遇到CORS错误，请使用代理服务器模式

## 项目结构

```
btc-monitor/
├── index.html          # 主页面
├── monitor.js          # 监控逻辑
├── proxy-server.js     # 代理服务器
├── package.json        # 项目配置
└── README.md          # 说明文档
```

## 常见问题

**Q: 为什么价格显示"获取失败"？**
A: 可能是CORS限制，请使用代理服务器模式运行。

**Q: 如何修改报警声音？**
A: 可以在 `monitor.js` 的 `playAlertSound` 函数中自定义。

**Q: 图表显示多少历史数据？**
A: 默认显示最近50个数据点，可在代码中调整。

## 许可证

MIT License