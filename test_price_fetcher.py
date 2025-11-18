#!/usr/bin/env python3
"""
测试价格获取功能
"""
from price_fetcher import PriceFetcher
import time

def test_price_fetcher():
    print("=" * 50)
    print("BTC价差监控系统 - 价格获取测试")
    print("=" * 50)
    
    fetcher = PriceFetcher()
    
    try:
        print("\n正在获取Backpack交易所价格...")
        backpack_price = fetcher.get_backpack_price()
        if backpack_price:
            print(f"✓ Backpack价格: ${backpack_price:,.2f}")
        else:
            print("✗ 无法获取Backpack价格")
        
        print("\n正在获取Lighter交易所价格...")
        lighter_price = fetcher.get_lighter_price()
        if lighter_price:
            print(f"✓ Lighter价格: ${lighter_price:,.2f}")
        else:
            print("✗ 无法获取Lighter价格")
        
        if backpack_price and lighter_price:
            difference = backpack_price - lighter_price
            difference_percent = (difference / lighter_price) * 100
            print("\n" + "=" * 50)
            print("价差分析:")
            print(f"  价差: ${difference:,.2f}")
            print(f"  价差百分比: {difference_percent:.4f}%")
            print("=" * 50)
        else:
            print("\n警告: 无法计算价差（价格获取不完整）")
    
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n清理资源...")
        fetcher.close()
        print("测试完成！")

if __name__ == "__main__":
    test_price_fetcher()
