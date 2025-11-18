# BTC价差监控工具 - 快速开始

## 🚀 快速启动（仅需3步）

### 步骤1: 检查Python环境

```bash
python3 --version
# 需要 Python 3.7 或更高版本
```

### 步骤2: 安装依赖

```bash
pip3 install -r requirements.txt

# Ubuntu/Debian系统还需要安装：
sudo apt-get install python3-tk
```

### 步骤3: 启动程序

**方式1 - 使用启动脚本（推荐）:**
```bash
./start_monitor.sh
```

**方式2 - 直接运行Python脚本:**
```bash
python3 btc_monitor.py
```

---

## 📊 功能预览

启动后，你将看到：

1. **实时价格显示**
   - Backpack Exchange 的 BTC 价格
   - Lighter（或参考价格）的 BTC 价格
   - 价格差异（美元 + 百分比）

2. **控制面板**
   - 🟢 开始监控 - 自动定时刷新
   - 🔴 停止监控 - 暂停自动刷新
   - 🔵 立即刷新 - 手动更新一次
   - 📥 导出数据 - 保存为CSV文件

3. **历史记录表格**
   - 自动每小时记录一次
   - 显示时间、价格、价差

---

## ⚙️ 使用技巧

### 调整刷新间隔
- 默认每10秒刷新一次
- 可在"刷新间隔"输入框中修改
- 建议不要设置太短（避免API限制）

### 数据记录
- 程序会每1小时自动记录一次数据
- 记录会显示在历史表格中
- 点击"导出数据"可保存所有记录

### 导出的CSV文件
- 文件名格式: `btc_price_diff_YYYYMMDD_HHMMSS.csv`
- 可用Excel、Google Sheets等打开
- 包含完整的时间戳和价格信息

---

## ❓ 常见问题

### Q: 显示"获取失败"怎么办？
A: 检查网络连接，程序会自动尝试备用API

### Q: 价格来源是哪里？
A: 
- Backpack: 官方API
- Lighter: 优先使用官方API，不可用时使用CoinGecko或Binance作为参考

### Q: 可以一直运行吗？
A: 可以，程序会持续监控并每小时自动记录数据

### Q: 如何停止程序？
A: 点击"停止监控"按钮，或直接关闭窗口

---

## 📝 示例场景

**场景1: 短期监控**
1. 启动程序
2. 点击"开始监控"
3. 观察实时价差
4. 需要时点击"导出数据"

**场景2: 长期跟踪**
1. 启动程序并开始监控
2. 让程序在后台运行
3. 每小时自动记录数据
4. 一天后导出查看趋势

---

## 🛠️ 故障排除

### 依赖安装失败
```bash
# 尝试升级pip
pip3 install --upgrade pip

# 重新安装依赖
pip3 install -r requirements.txt --force-reinstall
```

### tkinter相关错误
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora/RHEL
sudo dnf install python3-tkinter

# macOS (通常已内置)
# 如果没有，通过homebrew安装: brew install python-tk
```

### 网络连接问题
- 确保可以访问互联网
- 检查防火墙设置
- 尝试使用代理（如需要）

---

## 📧 需要帮助？

查看完整文档: [BTC_MONITOR_README.md](./BTC_MONITOR_README.md)

---

**享受监控！** 🎉
