#!/bin/bash
# BTC价差监控系统启动脚本

echo "BTC价差监控系统"
echo "=================="

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查依赖是否安装
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "警告: tkinter未安装，正在尝试安装..."
    # 根据系统不同，安装命令可能不同
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y python3-tk
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3-tkinter
    fi
fi

# 安装Python依赖
echo "正在安装Python依赖..."
pip3 install -r requirements.txt

# 运行程序
echo "启动监控程序..."
python3 btc_monitor.py
