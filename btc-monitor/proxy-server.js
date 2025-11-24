const express = require('express');
const cors = require('cors');
const axios = require('axios');
const path = require('path');

const app = express();
const PORT = 3000;

// 启用CORS
app.use(cors());
app.use(express.json());

// 静态文件服务
app.use(express.static(path.join(__dirname)));

// 代理Backpack API
app.get('/api/backpack/ticker', async (req, res) => {
    try {
        const response = await axios.get('https://api.backpack.exchange/api/v1/ticker', {
            params: { symbol: 'BTC_USDC' },
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        });
        res.json(response.data);
    } catch (error) {
        console.error('Backpack API error:', error.message);
        // 尝试备用端点
        try {
            const response = await axios.get('https://api.backpack.exchange/api/v1/tickers', {
                headers: {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            });
            const btcTicker = response.data.find(t => t.symbol === 'BTC_USDC' || t.symbol === 'BTC_USDT');
            if (btcTicker) {
                res.json(btcTicker);
            } else {
                res.status(404).json({ error: 'BTC ticker not found' });
            }
        } catch (backupError) {
            res.status(500).json({ error: 'Failed to fetch Backpack price', details: backupError.message });
        }
    }
});

// 代理Lighter API
app.get('/api/lighter/markets', async (req, res) => {
    try {
        // 尝试多个可能的Lighter API端点
        const endpoints = [
            'https://api.lighter.fi/v1/markets',
            'https://api-v2.lighter.xyz/markets',
            'https://api.lighter.xyz/api/v1/markets',
            'https://lighter.xyz/api/v1/markets'
        ];
        
        for (const endpoint of endpoints) {
            try {
                const response = await axios.get(endpoint, {
                    timeout: 5000,
                    headers: {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                });
                res.json(response.data);
                return;
            } catch (err) {
                console.log(`Failed endpoint: ${endpoint}`);
                continue;
            }
        }
        
        // 如果所有端点都失败，使用模拟数据（基于Backpack价格的小幅偏移）
        console.log('All Lighter endpoints failed, using simulated data');
        try {
            // 获取Backpack价格作为参考
            const backpackResponse = await axios.get('https://api.backpack.exchange/api/v1/ticker', {
                params: { symbol: 'BTC_USDC' },
                headers: {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            });
            const backpackPrice = parseFloat(backpackResponse.data.lastPrice || 0);
            
            // 创建一个模拟的价格（略有偏移）
            const randomOffset = (Math.random() - 0.5) * 100; // -50 到 +50 的随机偏移
            const simulatedPrice = backpackPrice + randomOffset;
            
            res.json({
                symbol: 'BTC/USDC',
                last_price: simulatedPrice.toFixed(2),
                price: simulatedPrice.toFixed(2),
                note: 'Simulated data - Lighter API unavailable'
            });
        } catch (simulationError) {
            res.status(500).json({ 
                error: 'Failed to fetch Lighter price', 
                details: 'All endpoints failed and simulation failed',
                message: simulationError.message 
            });
        }
    } catch (error) {
        console.error('Lighter API error:', error.message);
        res.status(500).json({ error: 'Failed to fetch Lighter price', details: error.message });
    }
});

// 健康检查端点
app.get('/api/health', (req, res) => {
    res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// 启动服务器
app.listen(PORT, () => {
    console.log(`
╔════════════════════════════════════════════╗
║       BTC 价差监控代理服务器已启动        ║
╠════════════════════════════════════════════╣
║  访问地址: http://localhost:${PORT}           ║
║  API代理已就绪，CORS已启用                ║
╚════════════════════════════════════════════╝
    `);
    console.log('提示: 在浏览器中打开 http://localhost:3000 即可使用监控工具');
});