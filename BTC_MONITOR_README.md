# BTC价差监控工具

一个用于监控 Backpack Exchange 和 Lighter 交易所之间BTC价格差异的GUI工具。

## 功能特点

- ✅ 实时监控两个交易所的BTC价格
- ✅ 自动计算价格差异和百分比
- ✅ 每小时自动记录价格数据
- ✅ 图形化界面，操作简单直观
- ✅ 历史数据表格显示
- ✅ 支持导出数据到CSV文件
- ✅ 可自定义刷新间隔

## 交易所信息

- **Backpack Exchange**: https://backpack.exchange/trade/BTC_USD_PERP
- **Lighter**: https://app.lighter.xyz/trade/BTC

## 安装步骤

### 1. 确保已安装Python 3.7+

```bash
python3 --version
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

或手动安装：

```bash
pip install requests pandas websocket-client
```

### 3. 运行程序

```bash
python3 btc_monitor.py
```

## 使用说明

### 界面说明

1. **实时价格区域**
   - 显示Backpack和Lighter的当前BTC价格
   - 显示价格差异（美元和百分比）
   - 显示最后更新时间

2. **控制按钮**
   - **开始监控**: 启动自动监控，按设定间隔刷新价格
   - **停止监控**: 停止自动监控
   - **立即刷新**: 手动刷新一次价格数据
   - **导出数据**: 将历史记录导出为CSV文件

3. **设置区域**
   - **刷新间隔**: 设置自动刷新的时间间隔（秒），默认10秒
   - 记录间隔固定为每1小时

4. **历史记录表格**
   - 显示每小时自动记录的价格数据
   - 包含时间戳、两个交易所价格、价差和价差百分比
   - 最新记录显示在顶部

### 使用流程

1. 启动程序后，点击"开始监控"按钮
2. 程序会每隔设定时间（默认10秒）自动刷新价格
3. 每小时自动记录一次数据到历史表格
4. 可以随时点击"立即刷新"手动更新价格
5. 点击"导出数据"可将历史记录保存为CSV文件
6. 点击"停止监控"停止自动刷新

### 数据导出

导出的CSV文件包含以下字段：
- `timestamp`: 记录时间
- `backpack`: Backpack交易所价格
- `lighter`: Lighter交易所价格
- `diff`: 价格差异（Backpack - Lighter）
- `diff_percent`: 价格差异百分比

文件名格式：`btc_price_diff_YYYYMMDD_HHMMSS.csv`

## API说明

### Backpack Exchange API

- **端点**: `https://api.backpack.exchange/api/v1/ticker`
- **交易对**: BTC_USDC
- **获取字段**: lastPrice（最后成交价）

### Lighter API (带备用方案)

工具会按以下顺序尝试获取Lighter价格：

1. **主要方案 - Lighter官方API**
   - 端点: `https://api.lighter.xyz/v1/tickers`
   - 交易对: BTC相关交易对

2. **备用方案1 - CoinGecko API**
   - 端点: `https://api.coingecko.com/api/v3/simple/price`
   - 用途: 当Lighter API不可用时，使用市场平均价格作为参考

3. **备用方案2 - Binance API**
   - 端点: `https://api.binance.com/api/v3/ticker/price`
   - 交易对: BTCUSDT
   - 用途: 作为最终备用价格源

> **注意**: 如果Lighter API暂时不可用，程序会自动切换到备用价格源，并在界面上提示。备用价格同样可以用于价差对比参考。

## 注意事项

1. **网络连接**: 确保网络连接稳定，程序需要访问交易所API
2. **API限制**: 注意交易所可能有API调用频率限制，建议刷新间隔不要设置过短
3. **价格差异**: 价格差异可能为正或负：
   - 正值：Backpack价格高于Lighter
   - 负值：Lighter价格高于Backpack
4. **数据准确性**: 价格数据来自交易所公开API，仅供参考

## 故障排除

### 价格显示"获取失败"

- 检查网络连接
- 确认交易所API是否正常工作
- 尝试增加刷新间隔

### 程序无响应

- 检查是否有防火墙阻止网络请求
- 确认Python依赖已正确安装
- 查看终端是否有错误信息

### 无法导出数据

- 确认当前目录有写入权限
- 检查是否有足够的磁盘空间

## 技术栈

- **Python 3.7+**
- **tkinter**: GUI界面
- **requests**: HTTP请求
- **pandas**: 数据处理和导出

## 开发者信息

本工具为开源项目，如有问题或建议，欢迎提出。

## 许可证

MIT License

## 更新日志

### v1.0.0 (2025-11-18)
- 首次发布
- 支持Backpack和Lighter交易所
- GUI界面
- 每小时自动记录
- CSV数据导出
