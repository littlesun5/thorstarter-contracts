# BTC价格监控工具

监控Backpack和Lighter交易所的BTC价格差，当价差超出设定阈值时发出提醒。

## 功能特性

- ✅ 实时监控Backpack和Lighter交易所的BTC价格
- ✅ 计算两个交易所之间的价差
- ✅ 当价差 > $80 或 < $10 时弹窗提醒
- ✅ 支持自定义监控间隔和阈值
- ✅ 防止频繁弹窗（60秒冷却时间）
- ✅ 实时控制台输出价格信息

## 安装依赖

```bash
pip install -r requirements.txt
```

或者手动安装：

```bash
pip install requests plyer
```

**注意**: `plyer`用于桌面弹窗提醒。如果安装失败，程序会自动降级为控制台输出。

## 使用方法

### 基本使用

```bash
python btc_monitor.py
```

### 自定义配置

在`btc_monitor.py`文件中修改以下参数：

```python
HIGH_THRESHOLD = 80   # 价差上限（美元），超过此值会提醒
LOW_THRESHOLD = 10    # 价差下限（美元），低于此值会提醒
CHECK_INTERVAL = 5    # 检查间隔（秒）
```

## API说明

### Backpack Exchange API
- 端点: `https://api.backpack.exchange/api/v1/ticker`
- 交易对: BTC_USDC
- 文档: https://docs.backpack.exchange/

### Lighter API
- 端点: `https://api.lighter.xyz/v1/ticker`
- 交易对: BTC_USDC
- 文档: https://apidocs.lighter.xyz/docs/get-started-for-programmers-1

## 输出示例

```
============================================================
BTC价格监控器已启动
监控交易所: Backpack 和 Lighter
价差阈值: > $80 或 < $10
检查间隔: 5秒
============================================================

[2025-11-24 10:30:15]
  Backpack: $96,500.00
  Lighter:  $96,425.00
  价差:     $75.00

[2025-11-24 10:30:20]
  Backpack: $96,550.00
  Lighter:  $96,460.00
  价差:     $90.00
  
【警告】价差过大！
Backpack: $96,550.00
Lighter: $96,460.00
价差: $90.00 (> $80)
```

## 停止监控

按 `Ctrl+C` 停止监控程序。

## 故障排除

### 1. 无法获取价格数据

可能的原因：
- 网络连接问题
- API端点变更
- API限流

解决方法：
- 检查网络连接
- 查看最新API文档确认端点是否变更
- 增加`CHECK_INTERVAL`减少请求频率

### 2. 弹窗提醒不工作

可能的原因：
- `plyer`库未正确安装
- 操作系统不支持桌面通知

解决方法：
- 重新安装：`pip install --upgrade plyer`
- Linux用户可能需要安装：`sudo apt-get install libnotify-bin`
- 程序会自动降级为控制台输出

### 3. API返回数据格式不匹配

由于API可能更新，如果价格获取失败，请：
1. 检查API文档获取最新的数据结构
2. 修改`get_backpack_btc_price()`或`get_lighter_btc_price()`方法
3. 更新相应的字段名称

## 自定义开发

### 添加更多交易所

在`BTCPriceMonitor`类中添加新的方法：

```python
def get_exchange_btc_price(self):
    try:
        response = requests.get("API_ENDPOINT", timeout=10)
        data = response.json()
        return float(data['price'])
    except Exception as e:
        print(f"获取价格失败: {e}")
        return None
```

### 修改提醒条件

在`check_prices()`方法中自定义判断逻辑：

```python
# 例如：只在价差过大时提醒
if spread > self.high_threshold:
    self.show_alert(message)
```

### 添加日志记录

```python
import logging

logging.basicConfig(
    filename='btc_monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# 在check_prices中添加
logging.info(f"Backpack: {backpack_price}, Lighter: {lighter_price}, Spread: {spread}")
```

## 许可证

MIT License
