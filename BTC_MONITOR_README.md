# BTC价差监控系统

这是一个用于监控Backpack和Lighter两个交易所BTC价格差异的GUI应用程序。

## 功能特点

- 📊 实时显示两个交易所的BTC价格
- 💰 自动计算并显示价差（美元和百分比）
- ⏰ 每小时自动记录价差数据
- 📈 历史数据表格展示
- 🎨 现代化的GUI界面

## 安装依赖

首先确保已安装Python 3.7+，然后安装所需依赖：

```bash
pip install -r requirements.txt
```

## 使用方法

运行主程序：

```bash
python btc_monitor.py
```

## 功能说明

### 界面说明

1. **实时价格显示区域**
   - Backpack交易所价格（蓝色）
   - Lighter交易所价格（红色）
   - 价差显示（绿色）

2. **控制按钮**
   - **开始监控**: 启动每小时自动记录功能
   - **停止监控**: 停止自动记录
   - **立即刷新**: 手动获取最新价格

3. **历史数据表格**
   - 显示所有记录的历史价差数据
   - 包含时间、两个交易所价格、价差和价差百分比

### 数据存储

所有数据自动保存到 `btc_price_data.csv` 文件中，包含以下字段：
- 时间
- Backpack价格
- Lighter价格
- 价差(USD)
- 价差百分比(%)

## 注意事项

1. 首次运行时会自动下载ChromeDriver（用于网页抓取）
2. 程序使用无头浏览器模式，不会显示浏览器窗口
3. 如果价格获取失败，请检查网络连接
4. 某些网站可能有反爬虫机制，如果频繁失败，可以尝试增加等待时间

## 故障排除

如果遇到问题：

1. **价格获取失败**
   - 检查网络连接
   - 确认目标网站可访问
   - 查看控制台日志输出

2. **ChromeDriver问题**
   - 确保已安装Chrome浏览器
   - 程序会自动下载匹配的ChromeDriver

3. **GUI界面问题**
   - 确保系统支持tkinter（通常Python自带）
   - Linux系统可能需要安装: `sudo apt-get install python3-tk`

## 技术栈

- Python 3.7+
- tkinter (GUI)
- Selenium (网页抓取)
- BeautifulSoup4 (HTML解析)
- pandas (数据处理)
- schedule (定时任务)
