#!/bin/bash
# BTC价格监控脚本 - 快速启动脚本

echo "=========================================="
echo "BTC价格监控脚本 - 快速启动"
echo "=========================================="
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3"
    exit 1
fi

echo "✓ Python版本: $(python3 --version)"

# 检查依赖
echo ""
echo "检查依赖包..."
python3 -c "import tkinter" 2>/dev/null && echo "✓ tkinter" || echo "✗ tkinter (需要安装: sudo apt-get install python3-tk)"
python3 -c "import requests" 2>/dev/null && echo "✓ requests" || echo "✗ requests"
python3 -c "import selenium" 2>/dev/null && echo "✓ selenium" || echo "✗ selenium"
python3 -c "import pandas" 2>/dev/null && echo "✓ pandas" || echo "✗ pandas"

echo ""
echo "启动监控程序..."
echo ""

# 运行脚本
python3 btc_price_monitor.py
