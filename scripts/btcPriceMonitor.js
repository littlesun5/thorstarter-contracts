const axios = require('axios');
const notifier = require('node-notifier');
const path = require('path');
const config = require('./btcPriceMonitor.config.js');

// 使用配置文件
const CONFIG = {
  CHECK_INTERVAL: config.checkInterval,
  PRICE_DIFF_THRESHOLD_HIGH: config.priceDiffThresholdHigh,
  PRICE_DIFF_THRESHOLD_LOW: config.priceDiffThresholdLow,
  ALERT_COOLDOWN: config.alert.cooldown,
};

// 获取Backpack的BTC价格
async function getBackpackPrice() {
  const bpConfig = config.backpack;
  const url = `${bpConfig.baseUrl}${bpConfig.tickerEndpoint}`;
  
  try {
    // 尝试多种可能的API格式
    let response;
    const params = { symbol: bpConfig.symbol };
    
    // 如果API需要认证，添加认证头
    const headers = {};
    if (bpConfig.apiKey && bpConfig.apiSecret) {
      // 根据实际API文档实现认证逻辑
      headers['X-API-KEY'] = bpConfig.apiKey;
    }
    
    response = await axios.get(url, { params, headers, timeout: 10000 });
    
    // 尝试解析多种可能的价格字段格式
    let price;
    const data = response.data;
    
    // 如果是数组格式
    if (Array.isArray(data) && data.length > 0) {
      price = parseFloat(data[0].last || data[0].price || data[0].close);
    }
    // 如果是对象格式
    else if (typeof data === 'object') {
      price = parseFloat(
        data.last || 
        data.price || 
        data.close || 
        data.lastPrice ||
        data.markPrice ||
        (data.result && (data.result.last || data.result.price))
      );
    }
    
    if (!price || isNaN(price)) {
      console.error('Backpack API响应数据:', JSON.stringify(data, null, 2));
      throw new Error('无法解析Backpack价格数据，请检查API响应格式');
    }
    
    return price;
  } catch (error) {
    console.error('获取Backpack价格失败:', error.message);
    if (error.response) {
      console.error('API状态码:', error.response.status);
      console.error('API响应:', JSON.stringify(error.response.data, null, 2));
    } else if (error.request) {
      console.error('请求失败，无法连接到API:', url);
    }
    throw error;
  }
}

// 获取Lighter的BTC价格
async function getLighterPrice() {
  const liConfig = config.lighter;
  const url = `${liConfig.baseUrl}${liConfig.tickerEndpoint}`;
  
  try {
    let response;
    const params = { symbol: liConfig.symbol };
    
    // 如果API需要认证
    const headers = {};
    if (liConfig.apiKey && liConfig.apiSecret) {
      headers['X-API-KEY'] = liConfig.apiKey;
      // 根据实际API文档实现认证逻辑
    }
    
    response = await axios.get(url, { params, headers, timeout: 10000 });
    
    // 尝试解析多种可能的价格字段格式
    let price;
    const data = response.data;
    
    // 如果是数组格式
    if (Array.isArray(data) && data.length > 0) {
      price = parseFloat(data[0].last || data[0].price || data[0].close || data[0].lastPrice);
    }
    // 如果是对象格式
    else if (typeof data === 'object') {
      price = parseFloat(
        data.last || 
        data.price || 
        data.close || 
        data.lastPrice ||
        data.markPrice ||
        (data.result && (data.result.last || data.result.price || data.result.lastPrice))
      );
    }
    
    if (!price || isNaN(price)) {
      console.error('Lighter API响应数据:', JSON.stringify(data, null, 2));
      throw new Error('无法解析Lighter价格数据，请检查API响应格式');
    }
    
    return price;
  } catch (error) {
    console.error('获取Lighter价格失败:', error.message);
    if (error.response) {
      console.error('API状态码:', error.response.status);
      console.error('API响应:', JSON.stringify(error.response.data, null, 2));
    } else if (error.request) {
      console.error('请求失败，无法连接到API:', url);
    }
    throw error;
  }
}

// 显示弹窗提醒
function showAlert(title, message, type = 'info') {
  notifier.notify({
    title: title,
    message: message,
    sound: config.alert.sound,
    wait: false,
    timeout: config.alert.timeout,
  });
  
  // 同时在控制台输出
  console.log(`\n🚨 ${title}`);
  console.log(`   ${message}\n`);
}

// 监控主函数
async function monitorPriceDifference() {
  let lastAlertTime = 0;
  
  console.log('🚀 BTC价差监控工具启动');
  console.log(`📊 监控间隔: ${CONFIG.CHECK_INTERVAL / 1000}秒`);
  console.log(`⚠️  价差阈值: > $${CONFIG.PRICE_DIFF_THRESHOLD_HIGH} 或 < $${CONFIG.PRICE_DIFF_THRESHOLD_LOW}`);
  console.log(`🔔 提醒冷却时间: ${CONFIG.ALERT_COOLDOWN / 1000}秒\n`);
  
  while (true) {
    try {
      // 获取两个交易所的价格
      const [backpackPrice, lighterPrice] = await Promise.all([
        getBackpackPrice(),
        getLighterPrice()
      ]);
      
      // 计算价差
      const priceDiff = Math.abs(backpackPrice - lighterPrice);
      const diffPercentage = ((priceDiff / Math.min(backpackPrice, lighterPrice)) * 100).toFixed(2);
      
      // 显示当前价格信息
      const timestamp = new Date().toLocaleTimeString('zh-CN');
      console.log(`[${timestamp}] Backpack: $${backpackPrice.toFixed(2)} | Lighter: $${lighterPrice.toFixed(2)} | 价差: $${priceDiff.toFixed(2)} (${diffPercentage}%)`);
      
      // 检查是否需要提醒
      const now = Date.now();
      const shouldAlert = (priceDiff > CONFIG.PRICE_DIFF_THRESHOLD_HIGH || priceDiff < CONFIG.PRICE_DIFF_THRESHOLD_LOW) &&
                         (now - lastAlertTime > CONFIG.ALERT_COOLDOWN);
      
      if (shouldAlert) {
        let alertTitle, alertMessage;
        
        if (priceDiff > CONFIG.PRICE_DIFF_THRESHOLD_HIGH) {
          alertTitle = '⚠️ 价差过大警告';
          alertMessage = `BTC价差已达到 $${priceDiff.toFixed(2)}！\n` +
                        `Backpack: $${backpackPrice.toFixed(2)}\n` +
                        `Lighter: $${lighterPrice.toFixed(2)}`;
        } else if (priceDiff < CONFIG.PRICE_DIFF_THRESHOLD_LOW) {
          alertTitle = '⚠️ 价差过小警告';
          alertMessage = `BTC价差仅为 $${priceDiff.toFixed(2)}！\n` +
                        `Backpack: $${backpackPrice.toFixed(2)}\n` +
                        `Lighter: $${lighterPrice.toFixed(2)}`;
        }
        
        showAlert(alertTitle, alertMessage);
        lastAlertTime = now;
      }
      
    } catch (error) {
      console.error(`[${new Date().toLocaleTimeString('zh-CN')}] 获取价格失败:`, error.message);
      // 出错时等待更长时间再重试
      await new Promise(resolve => setTimeout(resolve, CONFIG.CHECK_INTERVAL * 2));
      continue;
    }
    
    // 等待下一次检查
    await new Promise(resolve => setTimeout(resolve, CONFIG.CHECK_INTERVAL));
  }
}

// 启动监控
if (require.main === module) {
  monitorPriceDifference().catch(error => {
    console.error('监控程序出错:', error);
    process.exit(1);
  });
}

module.exports = { monitorPriceDifference, getBackpackPrice, getLighterPrice };
