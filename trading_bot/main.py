"""
交易机器人启动脚本
"""
import os
import sys
from dotenv import load_dotenv
from trading_bot import TradingBot

def main():
    """主函数"""
    # 加载环境变量
    load_dotenv()
    
    # 从环境变量获取API密钥
    api_key = os.getenv("BACKPACK_API_KEY")
    secret_key = os.getenv("BACKPACK_SECRET_KEY")
    
    if not api_key or not secret_key:
        print("错误: 请在.env文件中设置BACKPACK_API_KEY和BACKPACK_SECRET_KEY")
        print("示例:")
        print("BACKPACK_API_KEY=your_api_key")
        print("BACKPACK_SECRET_KEY=your_secret_key")
        sys.exit(1)
    
    # 检查是否为模拟模式
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
    
    print("=" * 60)
    print("RSI交易机器人")
    print("=" * 60)
    print(f"模拟模式: {dry_run}")
    print()
    
    if not dry_run:
        confirm = input("⚠️  您正在使用真实交易模式！确认继续吗？(输入 YES 确认): ")
        if confirm != "YES":
            print("已取消")
            sys.exit(0)
    
    # 创建并启动交易机器人
    bot = TradingBot(api_key, secret_key, dry_run=dry_run)
    
    try:
        bot.start(interval=60)  # 每60秒检查一次
    except KeyboardInterrupt:
        print("\n收到中断信号，正在停止...")
        bot.stop()

if __name__ == "__main__":
    main()
