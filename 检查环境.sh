#!/bin/bash
# 检查BTC监控脚本运行环境

echo "=========================================="
echo "BTC价格监控脚本 - 环境检查"
echo "=========================================="
echo ""

# 检查Python
echo "1. Python环境:"
if command -v python3 &> /dev/null; then
    echo "   ✓ Python版本: $(python3 --version)"
else
    echo "   ✗ Python3未安装"
    exit 1
fi

# 检查Python包
echo ""
echo "2. Python依赖包:"
python3 -c "import tkinter" 2>/dev/null && echo "   ✓ tkinter" || echo "   ✗ tkinter (安装: sudo apt-get install python3-tk)"
python3 -c "import requests" 2>/dev/null && echo "   ✓ requests" || echo "   ✗ requests (安装: pip install requests)"
python3 -c "import selenium" 2>/dev/null && echo "   ✓ selenium" || echo "   ✗ selenium (安装: pip install selenium)"
python3 -c "import pandas" 2>/dev/null && echo "   ✓ pandas" || echo "   ✗ pandas (安装: pip install pandas)"
python3 -c "from bs4 import BeautifulSoup" 2>/dev/null && echo "   ✓ beautifulsoup4" || echo "   ✗ beautifulsoup4 (安装: pip install beautifulsoup4)"

# 检查ChromeDriver
echo ""
echo "3. ChromeDriver:"
if command -v chromedriver &> /dev/null; then
    echo "   ✓ ChromeDriver已安装"
    chromedriver --version 2>/dev/null | head -1
else
    echo "   ⚠ ChromeDriver未安装（可选，脚本会使用API方式）"
    echo "   安装方法: ./install_chromedriver.sh"
fi

# 检查Chrome浏览器
echo ""
echo "4. Chrome/Chromium浏览器:"
CHROME_FOUND=false
for cmd in google-chrome chromium-browser chromium; do
    if command -v $cmd &> /dev/null; then
        echo "   ✓ 找到: $cmd"
        $cmd --version 2>/dev/null | head -1
        CHROME_FOUND=true
        break
    fi
done
if [ "$CHROME_FOUND" = false ]; then
    echo "   ⚠ Chrome/Chromium未安装（可选，用于Selenium）"
fi

# 测试网络连接
echo ""
echo "5. 网络连接测试:"
if curl -s --head https://backpack.exchange | head -1 | grep -q "200 OK"; then
    echo "   ✓ 可以访问Backpack交易所"
else
    echo "   ✗ 无法访问Backpack交易所"
fi

if curl -s --head https://app.lighter.xyz | head -1 | grep -q -E "(200|301|302)"; then
    echo "   ✓ 可以访问Lighter交易所"
else
    echo "   ⚠ 无法访问Lighter交易所（可能是404，但网站可访问）"
fi

# 总结
echo ""
echo "=========================================="
echo "检查完成！"
echo "=========================================="
echo ""
echo "如果所有必需项都显示 ✓，可以运行:"
echo "  python3 btc_price_monitor.py"
echo ""
echo "如果缺少依赖，运行:"
echo "  pip install -r requirements.txt"
echo "  sudo apt-get install python3-tk"
echo ""
