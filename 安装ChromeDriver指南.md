# ChromeDriver 安装和配置指南

## Linux系统安装方法

### 方法1：使用包管理器安装（推荐）

#### Ubuntu/Debian系统：
```bash
# 更新包列表
sudo apt-get update

# 安装Chrome浏览器（如果还没有）
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt-get install -y ./google-chrome-stable_current_amd64.deb

# 安装ChromeDriver
sudo apt-get install -y chromium-chromedriver

# 或者使用snap安装
sudo snap install chromium
```

#### 验证安装：
```bash
chromedriver --version
```

### 方法2：手动下载安装

#### 步骤1：检查Chrome版本
```bash
google-chrome --version
# 或
chromium-browser --version
```

#### 步骤2：下载对应版本的ChromeDriver
访问：https://chromedriver.chromium.org/downloads

或者使用脚本自动下载：
```bash
# 获取Chrome版本
CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+\.\d+' | head -1)
echo "Chrome版本: $CHROME_VERSION"

# 下载ChromeDriver（需要根据实际版本调整）
wget https://chromedriver.storage.googleapis.com/LATEST_RELEASE
```

#### 步骤3：解压并移动到系统路径
```bash
# 解压下载的文件
unzip chromedriver_linux64.zip

# 移动到系统路径（需要root权限）
sudo mv chromedriver /usr/local/bin/

# 设置执行权限
sudo chmod +x /usr/local/bin/chromedriver
```

#### 步骤4：验证
```bash
chromedriver --version
```

### 方法3：使用webdriver-manager（Python包，自动管理）

```bash
pip install webdriver-manager
```

然后修改脚本使用webdriver-manager（我会更新脚本支持这个）

## Windows系统安装方法

### 步骤1：检查Chrome版本
1. 打开Chrome浏览器
2. 点击右上角三个点 → 设置 → 关于Chrome
3. 记下版本号（例如：120.0.6099.109）

### 步骤2：下载ChromeDriver
1. 访问：https://chromedriver.chromium.org/downloads
2. 下载与Chrome版本匹配的ChromeDriver
3. 解压得到 `chromedriver.exe`

### 步骤3：添加到PATH环境变量

#### 方法A：通过系统设置（推荐）
1. 将 `chromedriver.exe` 复制到某个文件夹，例如：
   - `C:\Program Files\ChromeDriver\`
   - 或 `C:\Users\你的用户名\chromedriver\`

2. 添加到PATH：
   - 右键"此电脑" → 属性
   - 高级系统设置 → 环境变量
   - 在"系统变量"中找到"Path"，点击"编辑"
   - 点击"新建"，输入ChromeDriver所在路径（如：`C:\Program Files\ChromeDriver\`）
   - 点击"确定"保存

3. 验证：
   - 打开新的命令提示符（cmd）
   - 输入：`chromedriver --version`
   - 如果显示版本号，说明配置成功

#### 方法B：临时添加到PATH（仅当前会话）
```cmd
set PATH=%PATH%;C:\Program Files\ChromeDriver\
chromedriver --version
```

#### 方法C：放在Python脚本同目录
将 `chromedriver.exe` 放在与 `btc_price_monitor.py` 相同的文件夹中，脚本会自动找到它。

## macOS系统安装方法

```bash
# 使用Homebrew安装（最简单）
brew install chromedriver

# 或者手动下载
# 1. 访问 https://chromedriver.chromium.org/downloads
# 2. 下载macOS版本
# 3. 解压后移动到 /usr/local/bin/
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
```

## 验证安装

运行以下命令验证ChromeDriver是否正确安装：

```bash
# Linux/macOS
chromedriver --version

# Windows
chromedriver.exe --version
```

如果显示版本号，说明安装成功！

## 常见问题

### Q: 提示"chromedriver: command not found"
A: ChromeDriver没有在PATH中，需要按照上述步骤添加到PATH

### Q: 版本不匹配错误
A: ChromeDriver版本必须与Chrome浏览器版本匹配，下载对应版本

### Q: 权限错误（Linux）
A: 运行 `sudo chmod +x /usr/local/bin/chromedriver` 添加执行权限

### Q: 不想安装ChromeDriver怎么办？
A: 脚本会自动尝试使用API方式获取价格，不依赖Selenium。如果API可用，ChromeDriver不是必需的。

## 快速检查脚本

运行以下命令检查环境：
```bash
python3 -c "
import sys
print('Python版本:', sys.version)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    print('✓ Selenium已安装')
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    try:
        driver = webdriver.Chrome(options=options)
        print('✓ ChromeDriver可用')
        driver.quit()
    except Exception as e:
        print('✗ ChromeDriver不可用:', e)
except ImportError:
    print('✗ Selenium未安装')
"
```
