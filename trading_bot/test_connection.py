"""
测试连接脚本 - 验证API配置是否正确
"""
import os
from dotenv import load_dotenv
from backpack_api import BackpackAPI
from binance_api import BinanceAPI
from config import SYMBOL

def test_backpack_connection(api_key: str, secret_key: str):
    """测试Backpack连接"""
    print("\n测试Backpack连接...")
    print("-" * 50)
    
    try:
        api = BackpackAPI(api_key, secret_key)
        
        # 测试获取ticker
        print("1. 获取Ticker信息...")
        ticker = api.get_ticker(SYMBOL)
        if ticker:
            print(f"   ✓ 成功获取价格: ${ticker.get('lastPrice', 'N/A')}")
        else:
            print("   ✗ 获取Ticker失败")
            return False
        
        # 测试获取余额（需要签名）
        print("2. 获取账户余额...")
        balance = api.get_balance()
        if balance:
            print(f"   ✓ 成功连接到账户")
            # 打印部分余额信息
            for asset in balance[:3]:  # 只显示前3个
                print(f"      {asset.get('asset')}: {asset.get('available')}")
        else:
            print("   ✗ 获取余额失败（请检查API密钥权限）")
            return False
        
        print("\n✓ Backpack连接测试通过！")
        return True
        
    except Exception as e:
        print(f"\n✗ Backpack连接测试失败: {e}")
        return False

def test_binance_connection():
    """测试币安连接"""
    print("\n测试币安连接...")
    print("-" * 50)
    
    try:
        api = BinanceAPI()
        
        # 测试获取价格
        print("1. 获取BTC价格...")
        price = api.get_ticker_price("BTCUSDT")
        if price:
            print(f"   ✓ 成功获取价格: ${price:.2f}")
        else:
            print("   ✗ 获取价格失败")
            return False
        
        # 测试获取K线
        print("2. 获取K线数据...")
        klines = api.get_klines("BTCUSDT", "1m", 5)
        if klines and len(klines) > 0:
            print(f"   ✓ 成功获取K线: {len(klines)}条")
        else:
            print("   ✗ 获取K线失败")
            return False
        
        print("\n✓ 币安连接测试通过！")
        return True
        
    except Exception as e:
        print(f"\n✗ 币安连接测试失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("API连接测试工具")
    print("=" * 60)
    
    # 加载环境变量
    load_dotenv()
    
    api_key = os.getenv("BACKPACK_API_KEY")
    secret_key = os.getenv("BACKPACK_SECRET_KEY")
    
    if not api_key or not secret_key:
        print("\n⚠️  错误: 未找到API密钥")
        print("请在.env文件中设置BACKPACK_API_KEY和BACKPACK_SECRET_KEY")
        return
    
    # 测试币安连接
    binance_ok = test_binance_connection()
    
    # 测试Backpack连接
    backpack_ok = test_backpack_connection(api_key, secret_key)
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"币安API:    {'✓ 正常' if binance_ok else '✗ 异常'}")
    print(f"Backpack API: {'✓ 正常' if backpack_ok else '✗ 异常'}")
    
    if binance_ok and backpack_ok:
        print("\n🎉 所有测试通过！可以启动交易机器人。")
        print("\n启动命令:")
        print("  python main.py")
    else:
        print("\n⚠️  部分测试失败，请检查配置后重试。")

if __name__ == "__main__":
    main()
