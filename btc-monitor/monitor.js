// 全局变量
let monitorInterval = null;
let isMonitoring = false;
let priceHistory = [];
let chartInstance = null;
let alertHistory = [];

// 检测是否通过代理服务器运行
const isUsingProxy = window.location.protocol === 'http:' && window.location.hostname === 'localhost';
const API_BASE = isUsingProxy ? '' : '';

// API配置
const API_CONFIGS = {
    backpack: {
        // 优先使用代理，否则直接访问（可能有CORS问题）
        getUrl: () => isUsingProxy ? '/api/backpack/ticker' : 'https://api.backpack.exchange/api/v1/ticker?symbol=BTC_USDC',
        parsePrice: (data) => {
            return parseFloat(data.lastPrice || data.last || 0);
        }
    },
    lighter: {
        getUrl: () => isUsingProxy ? '/api/lighter/markets' : 'https://api.lighter.xyz/v1/markets',
        parsePrice: (data) => {
            // 如果是数组，查找BTC市场
            if (Array.isArray(data)) {
                const btcMarket = data.find(market => 
                    market.symbol === 'BTC/USDC' || 
                    market.symbol === 'BTC-USDC' ||
                    (market.base_asset === 'BTC' && market.quote_asset === 'USDC')
                );
                if (btcMarket) {
                    return parseFloat(btcMarket.last_price || btcMarket.price || btcMarket.last || 0);
                }
            }
            // 如果直接是价格数据
            else if (data.last || data.price || data.lastPrice) {
                return parseFloat(data.last || data.price || data.lastPrice || 0);
            }
            return 0;
        }
    }
};

// 初始化图表
function initChart() {
    const ctx = document.getElementById('spreadChart').getContext('2d');
    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: '价差 (USD)',
                data: [],
                borderColor: 'rgb(102, 126, 234)',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 2,
                tension: 0.1,
                fill: true
            }, {
                label: '最小阈值',
                data: [],
                borderColor: 'rgba(255, 99, 132, 0.5)',
                borderDash: [5, 5],
                borderWidth: 1,
                pointRadius: 0,
                fill: false
            }, {
                label: '最大阈值',
                data: [],
                borderColor: 'rgba(255, 99, 132, 0.5)',
                borderDash: [5, 5],
                borderWidth: 1,
                pointRadius: 0,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '价差历史走势图'
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: '时间'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: '价差 (USD)'
                    }
                }
            }
        }
    });
}

// 获取Backpack价格
async function getBackpackPrice() {
    try {
        const response = await fetch(API_CONFIGS.backpack.getUrl());
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        const price = API_CONFIGS.backpack.parsePrice(data);
        if (price > 0) return price;
        throw new Error('Invalid price data');
    } catch (error) {
        console.error('获取Backpack价格失败:', error);
        
        // 如果不是使用代理，显示CORS提示
        if (!isUsingProxy) {
            console.log('提示: 如果遇到CORS错误，请运行代理服务器: npm start');
        }
        return null;
    }
}

// 获取Lighter价格
async function getLighterPrice() {
    try {
        const response = await fetch(API_CONFIGS.lighter.getUrl());
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        const price = API_CONFIGS.lighter.parsePrice(data);
        if (price > 0) return price;
        throw new Error('Invalid price data');
    } catch (error) {
        console.error('获取Lighter价格失败:', error);
        
        // 如果不是使用代理，显示CORS提示
        if (!isUsingProxy) {
            console.log('提示: 如果遇到CORS错误，请运行代理服务器: npm start');
        }
        return null;
    }
}

// 更新价格显示
function updatePriceDisplay(backpackPrice, lighterPrice) {
    const backpackElement = document.getElementById('backpack-price');
    const lighterElement = document.getElementById('lighter-price');
    const backpackTimeElement = document.getElementById('backpack-time');
    const lighterTimeElement = document.getElementById('lighter-time');
    
    const currentTime = new Date().toLocaleTimeString('zh-CN');
    
    if (backpackPrice !== null) {
        backpackElement.textContent = `$${backpackPrice.toFixed(2)}`;
        backpackTimeElement.textContent = `更新时间: ${currentTime}`;
    } else {
        backpackElement.textContent = '获取失败';
        backpackTimeElement.textContent = '无法连接到Backpack';
    }
    
    if (lighterPrice !== null) {
        lighterElement.textContent = `$${lighterPrice.toFixed(2)}`;
        lighterTimeElement.textContent = `更新时间: ${currentTime}`;
    } else {
        lighterElement.textContent = '获取失败';
        lighterTimeElement.textContent = '无法连接到Lighter';
    }
}

// 计算并显示价差
function calculateAndDisplaySpread(backpackPrice, lighterPrice) {
    if (backpackPrice === null || lighterPrice === null) {
        document.getElementById('spread-value').textContent = '--';
        document.getElementById('spread-percentage').textContent = '--';
        return null;
    }
    
    const spread = backpackPrice - lighterPrice;
    const spreadPercentage = (Math.abs(spread) / Math.min(backpackPrice, lighterPrice)) * 100;
    
    const spreadElement = document.getElementById('spread-value');
    const percentageElement = document.getElementById('spread-percentage');
    
    spreadElement.textContent = `$${spread.toFixed(2)}`;
    percentageElement.textContent = `(${spreadPercentage.toFixed(2)}%)`;
    
    return spread;
}

// 检查价差阈值并报警
function checkSpreadThreshold(spread) {
    if (spread === null) return;
    
    const minThreshold = parseFloat(document.getElementById('min-spread').value);
    const maxThreshold = parseFloat(document.getElementById('max-spread').value);
    const absSpread = Math.abs(spread);
    
    const spreadElement = document.getElementById('spread-value');
    
    if (absSpread < minThreshold || absSpread > maxThreshold) {
        spreadElement.className = 'spread-value warning';
        
        // 创建报警信息
        const alertMessage = absSpread < minThreshold ? 
            `价差过小: $${spread.toFixed(2)} (小于 $${minThreshold})` :
            `价差过大: $${spread.toFixed(2)} (大于 $${maxThreshold})`;
        
        // 弹窗提醒
        showAlert(alertMessage);
        
        // 添加到历史记录
        addAlertToHistory(alertMessage);
        
        // 浏览器通知（如果支持）
        if (Notification.permission === "granted") {
            new Notification("🚨 BTC价差报警", {
                body: alertMessage,
                icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>⚠️</text></svg>",
                requireInteraction: true
            });
        }
    } else {
        spreadElement.className = 'spread-value normal';
    }
}

// 显示弹窗提醒
function showAlert(message) {
    // 创建自定义弹窗
    const alertBox = document.createElement('div');
    alertBox.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        color: white;
        padding: 20px 30px;
        border-radius: 10px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        z-index: 10000;
        animation: slideIn 0.3s ease;
        font-size: 1.1em;
        font-weight: bold;
        max-width: 400px;
    `;
    alertBox.innerHTML = `
        <div style="display: flex; align-items: center;">
            <span style="font-size: 1.5em; margin-right: 10px;">⚠️</span>
            <div>
                <div>价差报警</div>
                <div style="font-size: 0.9em; font-weight: normal; margin-top: 5px;">${message}</div>
                <div style="font-size: 0.8em; font-weight: normal; margin-top: 5px; opacity: 0.9;">
                    ${new Date().toLocaleTimeString('zh-CN')}
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(alertBox);
    
    // 播放提示音
    playAlertSound();
    
    // 5秒后自动消失
    setTimeout(() => {
        alertBox.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(alertBox);
        }, 300);
    }, 5000);
}

// 播放提示音
function playAlertSound() {
    // 创建音频上下文
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    
    // 创建提示音
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
    oscillator.frequency.exponentialRampToValueAtTime(400, audioContext.currentTime + 0.5);
    
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
}

// 添加到报警历史
function addAlertToHistory(message) {
    const time = new Date().toLocaleString('zh-CN');
    alertHistory.unshift({ time, message });
    
    // 只保留最近20条记录
    if (alertHistory.length > 20) {
        alertHistory.pop();
    }
    
    updateAlertHistoryDisplay();
}

// 更新报警历史显示
function updateAlertHistoryDisplay() {
    const alertList = document.getElementById('alert-list');
    
    if (alertHistory.length === 0) {
        alertList.innerHTML = '<div style="color: #999;">暂无报警记录</div>';
        return;
    }
    
    alertList.innerHTML = alertHistory.map(alert => `
        <div class="alert-item">
            <div class="alert-time">${alert.time}</div>
            <div class="alert-message">${alert.message}</div>
        </div>
    `).join('');
}

// 更新图表
function updateChart(spread) {
    if (!chartInstance || spread === null) return;
    
    const now = new Date().toLocaleTimeString('zh-CN');
    const minThreshold = parseFloat(document.getElementById('min-spread').value);
    const maxThreshold = parseFloat(document.getElementById('max-spread').value);
    
    // 添加新数据点
    chartInstance.data.labels.push(now);
    chartInstance.data.datasets[0].data.push(Math.abs(spread));
    chartInstance.data.datasets[1].data.push(minThreshold);
    chartInstance.data.datasets[2].data.push(maxThreshold);
    
    // 只保留最近50个数据点
    if (chartInstance.data.labels.length > 50) {
        chartInstance.data.labels.shift();
        chartInstance.data.datasets.forEach(dataset => {
            dataset.data.shift();
        });
    }
    
    chartInstance.update();
}

// 监控循环
async function monitorPrices() {
    try {
        // 并行获取两个交易所的价格
        const [backpackPrice, lighterPrice] = await Promise.all([
            getBackpackPrice(),
            getLighterPrice()
        ]);
        
        // 更新显示
        updatePriceDisplay(backpackPrice, lighterPrice);
        
        // 计算价差
        const spread = calculateAndDisplaySpread(backpackPrice, lighterPrice);
        
        // 检查阈值
        checkSpreadThreshold(spread);
        
        // 更新图表
        updateChart(spread);
        
    } catch (error) {
        console.error('监控过程中出错:', error);
        
        // 显示错误提示
        if (!isUsingProxy) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.innerHTML = `
                <strong>提示:</strong> 可能遇到CORS错误。请按照以下步骤操作：<br>
                1. 打开终端并进入 btc-monitor 目录<br>
                2. 运行: npm install<br>
                3. 运行: npm start<br>
                4. 访问: http://localhost:3000
            `;
            
            // 只显示一次错误提示
            if (!document.querySelector('.error-message')) {
                document.querySelector('.container').insertBefore(errorDiv, document.querySelector('.price-display'));
            }
        }
    }
}

// 开始监控
async function startMonitoring() {
    if (isMonitoring) {
        showAlert('监控已在运行中');
        return;
    }
    
    // 请求通知权限
    if (Notification.permission === "default") {
        await Notification.requestPermission();
    }
    
    isMonitoring = true;
    const refreshInterval = parseInt(document.getElementById('refresh-interval').value) * 1000;
    
    // 立即执行一次
    await monitorPrices();
    
    // 设置定时器
    monitorInterval = setInterval(monitorPrices, refreshInterval);
    
    // 更新状态显示
    const statusElement = document.getElementById('status');
    statusElement.textContent = '🟢 监控运行中...';
    statusElement.className = 'status running';
}

// 停止监控
function stopMonitoring() {
    if (!isMonitoring) {
        showAlert('监控未在运行');
        return;
    }
    
    isMonitoring = false;
    
    if (monitorInterval) {
        clearInterval(monitorInterval);
        monitorInterval = null;
    }
    
    // 更新状态显示
    const statusElement = document.getElementById('status');
    statusElement.textContent = '⏸ 监控已停止';
    statusElement.className = 'status stopped';
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    
    // 添加CSS动画
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
    
    // 显示运行模式
    if (isUsingProxy) {
        console.log('✅ 正在通过代理服务器运行');
    } else {
        console.log('⚠️ 直接访问API模式（可能遇到CORS问题）');
        console.log('建议运行代理服务器: npm start');
    }
});

// 处理页面关闭
window.addEventListener('beforeunload', () => {
    stopMonitoring();
});