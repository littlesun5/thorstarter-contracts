#!/bin/bash

echo "=========================================="
echo "   BTC Price Monitor - API Test Script"
echo "=========================================="
echo ""

# Check server health
echo "1. Checking server health..."
health=$(curl -s http://localhost:3000/api/health 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "   OK: Server is running"
    echo "   Response: $health"
else
    echo "   ERROR: Server is not running. Please run: npm start"
    exit 1
fi
echo ""

# Get Backpack price
echo "2. Getting Backpack Exchange BTC price..."
backpack_response=$(curl -s http://localhost:3000/api/backpack/ticker 2>/dev/null)
if [ $? -eq 0 ]; then
    backpack_price=$(echo $backpack_response | python3 -c "import json, sys; data = json.load(sys.stdin); print(data.get('lastPrice', 'N/A'))")
    echo "   OK: Backpack BTC price: \$$backpack_price"
else
    echo "   ERROR: Unable to get Backpack price"
fi
echo ""

# Get Lighter price
echo "3. Getting Lighter BTC price..."
lighter_response=$(curl -s http://localhost:3000/api/lighter/markets 2>/dev/null)
if [ $? -eq 0 ]; then
    # Try to parse JSON
    lighter_price=$(echo $lighter_response | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if isinstance(data, dict):
        price = data.get('last_price') or data.get('price') or data.get('lastPrice', 'N/A')
    elif isinstance(data, list):
        btc_market = next((m for m in data if 'BTC' in str(m)), None)
        price = btc_market.get('last_price', 'N/A') if btc_market else 'N/A'
    else:
        price = 'N/A'
    print(price)
except:
    print('Parse failed')
" 2>/dev/null)
    
    if [ "$lighter_price" != "Parse failed" ] && [ "$lighter_price" != "" ]; then
        echo "   OK: Lighter BTC price: \$$lighter_price"
        
        # Check if simulated data
        if echo $lighter_response | grep -q "Simulated data"; then
            echo "   WARNING: Using simulated data (Lighter API unavailable)"
        fi
    else
        echo "   ERROR: Lighter API returned non-JSON data"
    fi
else
    echo "   ERROR: Unable to connect to Lighter API"
fi
echo ""

echo "=========================================="
echo "Test complete! Visit http://localhost:3000 to use the monitor"
echo "=========================================="