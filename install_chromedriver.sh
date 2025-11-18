#!/bin/bash
# ChromeDriver自动安装脚本（Linux）

echo "=========================================="
echo "ChromeDriver 自动安装脚本"
echo "=========================================="
echo ""

# 检查是否以root运行
if [ "$EUID" -ne 0 ]; then 
    echo "提示: 某些操作需要root权限，将使用sudo"
    SUDO="sudo"
else
    SUDO=""
fi

# 方法1: 尝试使用包管理器安装
echo "方法1: 尝试使用包管理器安装..."
if command -v apt-get &> /dev/null; then
    echo "检测到apt包管理器，尝试安装..."
    $SUDO apt-get update -qq
    $SUDO apt-get install -y chromium-chromedriver 2>/dev/null
    if command -v chromedriver &> /dev/null; then
        echo "✓ 安装成功！"
        chromedriver --version
        exit 0
    fi
elif command -v yum &> /dev/null; then
    echo "检测到yum包管理器..."
    $SUDO yum install -y chromium-chromedriver 2>/dev/null
    if command -v chromedriver &> /dev/null; then
        echo "✓ 安装成功！"
        chromedriver --version
        exit 0
    fi
fi

# 方法2: 检查是否已安装Chrome
echo ""
echo "方法2: 检查Chrome/Chromium安装..."
CHROME_CMD=""
for cmd in google-chrome chromium-browser chromium; do
    if command -v $cmd &> /dev/null; then
        CHROME_CMD=$cmd
        echo "找到: $cmd"
        $cmd --version
        break
    fi
done

if [ -z "$CHROME_CMD" ]; then
    echo "未找到Chrome/Chromium，尝试安装Chromium..."
    if command -v apt-get &> /dev/null; then
        $SUDO apt-get install -y chromium-browser
        CHROME_CMD="chromium-browser"
    fi
fi

# 方法3: 使用webdriver-manager（Python方式）
echo ""
echo "方法3: 使用webdriver-manager（推荐，自动管理版本）..."
pip3 install webdriver-manager --quiet 2>/dev/null
if python3 -c "from webdriver_manager.chrome import ChromeDriverManager; print('OK')" 2>/dev/null; then
    echo "✓ webdriver-manager已安装"
    echo "脚本将自动使用webdriver-manager管理ChromeDriver"
    exit 0
fi

# 方法4: 手动下载（最后手段）
echo ""
echo "方法4: 需要手动安装ChromeDriver"
echo "请访问: https://chromedriver.chromium.org/downloads"
echo "下载与Chrome版本匹配的ChromeDriver"
echo ""
echo "安装步骤:"
echo "1. 下载 chromedriver_linux64.zip"
echo "2. 解压: unzip chromedriver_linux64.zip"
echo "3. 移动到系统路径: sudo mv chromedriver /usr/local/bin/"
echo "4. 设置权限: sudo chmod +x /usr/local/bin/chromedriver"
echo "5. 验证: chromedriver --version"

echo ""
echo "=========================================="
echo "注意: 即使没有ChromeDriver，脚本也可以工作"
echo "脚本会优先使用API方式获取价格"
echo "=========================================="
