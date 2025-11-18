#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试BTC价格监控脚本的核心功能
"""

import sys
import requests
from datetime import datetime

def test_api_connections():
    """测试API连接"""
    print("=" * 60)
    print("测试API连接...")
    print("=" * 60)
    
    # 测试Backpack API
    print("\n1. 测试Backpack API...")
    try:
        api_url = "https://api.backpack.exchange/api/v1/ticker"
        response = requests.get(api_url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   返回数据条数: {len(data) if isinstance(data, list) else 'N/A'}")
            # 查找BTC相关的ticker
            btc_found = False
            for ticker in data[:10]:  # 只检查前10个
                symbol = ticker.get('symbol', '')
                if 'BTC' in symbol:
                    print(f"   找到BTC交易对: {symbol}")
                    print(f"   价格: ${ticker.get('lastPrice', 'N/A')}")
                    btc_found = True
                    break
            if not btc_found:
                print("   未在前10个交易对中找到BTC，但API连接正常")
        else:
            print(f"   API返回错误: {response.status_code}")
    except Exception as e:
        print(f"   错误: {e}")
    
    # 测试Lighter API
    print("\n2. 测试Lighter API...")
    try:
        api_urls = [
            "https://api.lighter.xyz/v1/markets",
            "https://api.lighter.xyz/v1/ticker",
        ]
        for api_url in api_urls:
            try:
                response = requests.get(api_url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                print(f"   {api_url}: 状态码 {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"   返回数据类型: {type(data).__name__}")
                    if isinstance(data, list) and len(data) > 0:
                        print(f"   数据条数: {len(data)}")
                        print(f"   第一个条目: {list(data[0].keys()) if data else 'N/A'}")
                    break
            except Exception as e:
                print(f"   {api_url} 错误: {e}")
                continue
    except Exception as e:
        print(f"   错误: {e}")
    
    # 测试网页访问
    print("\n3. 测试网页访问...")
    urls = [
        "https://backpack.exchange/trade/BTC_USD_PERP",
        "https://app.lighter.xyz/trade/BTC"
    ]
    for url in urls:
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            print(f"   {url}: 状态码 {response.status_code}")
        except Exception as e:
            print(f"   {url} 错误: {e}")

def test_imports():
    """测试导入"""
    print("\n" + "=" * 60)
    print("测试Python模块导入...")
    print("=" * 60)
    
    modules = [
        ('tkinter', 'GUI界面'),
        ('requests', 'HTTP请求'),
        ('bs4', 'HTML解析'),
        ('selenium', '浏览器自动化'),
        ('pandas', '数据处理'),
    ]
    
    for module_name, description in modules:
        try:
            if module_name == 'bs4':
                import bs4
            elif module_name == 'tkinter':
                import tkinter
            else:
                __import__(module_name)
            print(f"   ✓ {module_name:15} ({description}) - 已安装")
        except ImportError as e:
            print(f"   ✗ {module_name:15} ({description}) - 未安装: {e}")

def test_price_fetch():
    """测试价格获取功能"""
    print("\n" + "=" * 60)
    print("测试价格获取功能...")
    print("=" * 60)
    
    try:
        # 导入主脚本
        sys.path.insert(0, '/workspace')
        from btc_price_monitor import BTCPriceMonitor
        
        print("   脚本导入成功")
        print("   注意: GUI界面需要图形环境才能显示")
        print("   在命令行环境中，可以测试价格获取逻辑")
        
    except Exception as e:
        print(f"   导入错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("BTC价格监控脚本 - 测试程序")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 测试导入
    test_imports()
    
    # 测试API连接
    test_api_connections()
    
    # 测试价格获取
    test_price_fetch()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("\n使用说明:")
    print("1. 如果所有模块都已安装，可以运行: python btc_price_monitor.py")
    print("2. 如果缺少模块，运行: pip install -r requirements.txt")
    print("3. 如果ChromeDriver未安装，脚本会尝试使用API方式获取价格")
    print("=" * 60 + "\n")
