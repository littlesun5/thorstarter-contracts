#!/bin/bash

# BTC RSI 交易机器人安装脚本

echo "====================================="
echo "BTC RSI 交易机器人安装向导"
echo "====================================="
echo ""

# 检查Python版本
echo "检查Python版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python版本: $python_version"
echo ""

# 安装依赖
echo "安装Python依赖包..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✓ 依赖安装成功"
else
    echo "✗ 依赖安装失败，请检查网络或pip配置"
    exit 1
fi
echo ""

# 创建.env文件
if [ ! -f .env ]; then
    echo "创建环境配置文件..."
    cp .env.example .env
    echo "✓ .env文件已创建"
    echo ""
    echo "⚠️  请编辑.env文件，填入你的API密钥："
    echo "   nano .env"
    echo ""
else
    echo "✓ .env文件已存在"
    echo ""
fi

echo "====================================="
echo "安装完成！"
echo "====================================="
echo ""
echo "下一步："
echo "1. 编辑.env文件，填入你的Backpack API密钥"
echo "2. 运行测试: python test_connection.py"
echo "3. 启动机器人（模拟模式）: python main.py"
echo ""
echo "查看快速指南: cat QUICKSTART.md"
echo "查看完整文档: cat README.md"
echo ""
