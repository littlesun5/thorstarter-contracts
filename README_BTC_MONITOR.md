# BTC价格监控脚本

这是一个用于监控Backpack和Lighter两个交易所BTC价格差价的GUI应用程序。

## 功能特点

- 🔄 实时监控两个交易所的BTC价格
- 📊 自动计算并显示价差
- ⏰ 每小时自动记录一次价格数据
- 📈 历史数据表格展示
- 💾 自动保存历史数据到本地文件
- 🎨 友好的GUI界面

## 安装要求

### 1. Python环境
需要Python 3.7或更高版本

### 2. 安装依赖包
```bash
pip install -r requirements.txt
```

### 3. Chrome浏览器和ChromeDriver
脚本使用Selenium来抓取动态网页内容，需要：
- 安装Chrome浏览器
- 安装ChromeDriver（与Chrome版本匹配）

**安装ChromeDriver的方法：**

**Linux:**
```bash
# 使用apt安装（推荐）
sudo apt-get update
sudo apt-get install chromium-chromedriver

# 或手动下载
wget https://chromedriver.storage.googleapis.com/LATEST_RELEASE
# 然后下载对应版本的chromedriver
```

**macOS:**
```bash
brew install chromedriver
```

**Windows:**
1. 访问 https://chromedriver.chromium.org/downloads
2. 下载与你的Chrome版本匹配的ChromeDriver
3. 将chromedriver.exe放到PATH环境变量中

## 使用方法

### 运行脚本
```bash
python btc_price_monitor.py
```

### 界面操作

1. **查看实时价格**: 启动后会自动显示当前两个交易所的BTC价格和价差
2. **立即刷新**: 点击"立即刷新"按钮可以立即获取最新价格
3. **开始监控**: 点击"开始监控"按钮，程序将每小时自动记录一次价格数据
4. **停止监控**: 点击"停止监控"按钮可以停止自动监控
5. **查看历史**: 在表格中查看所有历史记录的价格数据

### 数据存储

- 历史数据自动保存到 `btc_price_data.json` 文件
- 数据格式为JSON，包含时间戳、价格和价差信息
- 程序重启后会自动加载历史数据

## 注意事项

1. **网络连接**: 需要稳定的网络连接来访问交易所网站
2. **ChromeDriver**: 如果Selenium无法工作，脚本会尝试使用API方式获取价格
3. **价格范围**: 脚本会验证价格是否在合理范围内（$10,000 - $200,000）
4. **数据更新**: 监控模式下每小时自动更新一次，也可以手动点击刷新

## 故障排除

### 如果无法获取价格：

1. **检查网络连接**: 确保可以访问两个交易所网站
2. **检查ChromeDriver**: 确保ChromeDriver已正确安装并在PATH中
3. **查看控制台输出**: 脚本会在控制台输出错误信息，帮助诊断问题
4. **尝试手动刷新**: 点击"立即刷新"按钮测试是否能获取价格

### 如果Selenium无法工作：

脚本会自动回退到使用API方式获取价格。如果两种方式都失败，请检查：
- 交易所网站是否可访问
- 是否有防火墙或代理限制
- 交易所API是否发生变化

## 技术说明

- **GUI框架**: Tkinter (Python内置)
- **网页抓取**: Selenium + BeautifulSoup
- **数据存储**: JSON格式
- **定时任务**: Python threading

## 许可证

MIT License
