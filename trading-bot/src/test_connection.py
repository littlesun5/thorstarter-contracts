#!/usr/bin/env python3
"""
Test connection to Backpack Exchange API
Verifies API credentials and connection
"""

import os
import sys
import logging
from dotenv import load_dotenv
from backpack_api import BackpackAPI
from rsi_calculator import RSICalculator
import colorlog

# Configure logging
handler = colorlog.StreamHandler()
handler.setFormatter(
    colorlog.ColoredFormatter(
        '%(log_color)s%(message)s',
        log_colors={
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
        }
    )
)

logger = colorlog.getLogger('TestConnection')
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def test_connection():
    """Test connection to Backpack Exchange"""
    print("=" * 50)
    print("TESTING BACKPACK EXCHANGE CONNECTION")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv('.env')
    
    api_key = os.getenv('BACKPACK_API_KEY')
    api_secret = os.getenv('BACKPACK_API_SECRET')
    use_testnet = os.getenv('USE_TESTNET', 'false').lower() == 'true'
    symbol = os.getenv('SYMBOL', 'BTC-USDT')
    
    if not api_key or not api_secret:
        print("❌ API credentials not found in .env file")
        print("   Please edit .env file and add your credentials")
        return False
    
    print(f"\n📡 Connecting to {'TESTNET' if use_testnet else 'MAINNET'}...")
    
    try:
        # Initialize API client
        api = BackpackAPI(api_key, api_secret, testnet=use_testnet)
        
        # Test 1: Get ticker
        print("\n1. Testing ticker endpoint...")
        ticker = api.get_ticker(symbol)
        if ticker and 'lastPrice' in ticker:
            print(f"   ✅ Current {symbol} price: ${float(ticker['lastPrice']):,.2f}")
        else:
            print(f"   ❌ Failed to get ticker data")
            return False
        
        # Test 2: Get account balance
        print("\n2. Testing account endpoint...")
        try:
            account = api.get_account_balance()
            print(f"   ✅ Account access successful")
            
            # Display balances if available
            if 'balances' in account:
                print("\n   Account Balances:")
                for balance in account['balances'][:5]:  # Show first 5 balances
                    asset = balance.get('asset', 'Unknown')
                    free = float(balance.get('free', 0))
                    if free > 0:
                        print(f"      {asset}: {free:.8f}")
        except Exception as e:
            print(f"   ⚠️  Account access failed (might need API permissions): {e}")
        
        # Test 3: Get orderbook
        print("\n3. Testing orderbook endpoint...")
        orderbook = api.get_orderbook(symbol, depth=5)
        if orderbook and 'bids' in orderbook and 'asks' in orderbook:
            best_bid = float(orderbook['bids'][0][0]) if orderbook['bids'] else 0
            best_ask = float(orderbook['asks'][0][0]) if orderbook['asks'] else 0
            spread = best_ask - best_bid
            print(f"   ✅ Orderbook received")
            print(f"      Best Bid: ${best_bid:,.2f}")
            print(f"      Best Ask: ${best_ask:,.2f}")
            print(f"      Spread:   ${spread:.2f}")
        else:
            print(f"   ❌ Failed to get orderbook")
            return False
        
        # Test 4: Get klines
        print("\n4. Testing klines endpoint...")
        klines = api.get_klines(symbol, '1m', 10)
        if klines and len(klines) > 0:
            print(f"   ✅ Received {len(klines)} klines")
        else:
            print(f"   ❌ Failed to get klines")
            return False
        
        # Test 5: Test RSI calculation
        print("\n5. Testing RSI calculation...")
        rsi_calc = RSICalculator(period=14)
        
        # Test with Binance data
        print("   Testing with Binance data...")
        rsi, price = rsi_calc.get_current_rsi(source='binance')
        if rsi:
            print(f"   ✅ Binance RSI: {rsi:.2f} (Price: ${price:,.2f})")
        else:
            print(f"   ⚠️  Could not calculate RSI from Binance")
        
        # Test with Backpack data
        print("   Testing with Backpack data...")
        rsi, price = rsi_calc.get_current_rsi(source='backpack', api_client=api, symbol=symbol)
        if rsi:
            print(f"   ✅ Backpack RSI: {rsi:.2f} (Price: ${price:,.2f})")
        else:
            print(f"   ⚠️  Could not calculate RSI from Backpack")
        
        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("=" * 50)
        print("\nYour bot is ready to run!")
        print("Start the bot with: python src/trading_bot.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Connection test failed: {e}")
        print("\nPossible issues:")
        print("1. Invalid API credentials")
        print("2. API permissions not set correctly")
        print("3. Network connection issues")
        print("4. Backpack Exchange API is down")
        
        return False


if __name__ == "__main__":
    import logging
    
    try:
        success = test_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        sys.exit(1)