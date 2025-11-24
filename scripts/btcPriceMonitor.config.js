// BTC价差监控工具配置文件
module.exports = {
  // 监控间隔（毫秒）
  checkInterval: 5000, // 5秒检查一次
  
  // 价差阈值（美元）
  priceDiffThresholdHigh: 80, // 大于此值时提醒
  priceDiffThresholdLow: 10,  // 小于此值时提醒
  
  // Backpack Exchange API配置
  backpack: {
    // 根据 https://docs.backpack.exchange/ 调整
    // 可能的端点格式:
    // - https://api.backpack.exchange/api/v1/ticker
    // - https://api.backpack.exchange/v1/ticker
    baseUrl: 'https://api.backpack.exchange',
    tickerEndpoint: '/api/v1/ticker', // 或 '/v1/ticker'
    symbol: 'BTC_USDC', // 交易对符号，根据实际API调整
    // 如果需要API密钥（通常公开数据不需要）
    apiKey: process.env.BACKPACK_API_KEY || '',
    apiSecret: process.env.BACKPACK_API_SECRET || '',
  },
  
  // Lighter Exchange API配置
  lighter: {
    // 根据 https://apidocs.lighter.xyz/ 调整
    // 可能的端点格式:
    // - https://api.lighter.xyz/v1/ticker
    // - https://api.lighter.xyz/public/ticker
    baseUrl: 'https://api.lighter.xyz',
    tickerEndpoint: '/v1/ticker', // 或 '/public/ticker'
    symbol: 'BTC-USDC', // 交易对符号，根据实际API调整
    // 如果需要API密钥
    apiKey: process.env.LIGHTER_API_KEY || '',
    apiSecret: process.env.LIGHTER_API_SECRET || '',
  },
  
  // 提醒设置
  alert: {
    cooldown: 60000, // 提醒冷却时间（毫秒），避免频繁提醒
    sound: true, // 是否播放声音
    timeout: 10, // 弹窗显示时间（秒）
  },
};
