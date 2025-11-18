#!/bin/bash
# BTC价差监控工具启动脚本

echo "=========================================="
echo "   BTC价差监控工具"
echo "   Backpack vs Lighter"
echo "=========================================="
echo ""

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    echo "请先安装 Python 3.7 或更高版本"
    exit 1
fi

echo "Python版本: $(python3 --version)"
echo ""

# 检查依赖
echo "检查依赖..."
python3 -c "
try:
    import tkinter
    import requests
    import pandas
    print('✓ 所有依赖已安装')
except ImportError as e:
    print(f'✗ 缺少依赖: {e}')
    print('请运行: pip3 install -r requirements.txt')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo ""
    echo "安装依赖..."
    pip3 install -r requirements.txt
fi

echo ""
echo "启动监控工具..."
echo ""

# 运行程序
python3 btc_monitor.py

echo ""
echo "程序已退出"
