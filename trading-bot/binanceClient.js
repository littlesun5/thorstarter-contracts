const axios = require('axios');

/**
 * Simple Binance client for fetching price data
 * Used as fallback if Backpack data is unavailable
 */
class BinanceClient {
  constructor() {
    this.baseURL = 'https://api.binance.com';
  }

  /**
   * Get klines (candlestick data) from Binance
   * @param {string} symbol - Trading pair (e.g., 'BTCUSDT')
   * @param {string} interval - Time interval (1m, 5m, etc.)
   * @param {number} limit - Number of candles to fetch
   */
  async getKlines(symbol = 'BTCUSDT', interval = '1m', limit = 100) {
    try {
      const response = await axios.get(`${this.baseURL}/api/v3/klines`, {
        params: { symbol, interval, limit }
      });
      
      // Convert Binance format to Backpack-like format
      return response.data.map(kline => ({
        open: parseFloat(kline[1]),
        high: parseFloat(kline[2]),
        low: parseFloat(kline[3]),
        close: parseFloat(kline[4]),
        volume: parseFloat(kline[5]),
        timestamp: kline[0]
      }));
    } catch (error) {
      console.error('Error fetching Binance klines:', error.response?.data || error.message);
      throw error;
    }
  }

  /**
   * Get current ticker price
   */
  async getTicker(symbol = 'BTCUSDT') {
    try {
      const response = await axios.get(`${this.baseURL}/api/v3/ticker/price`, {
        params: { symbol }
      });
      return { price: parseFloat(response.data.price) };
    } catch (error) {
      console.error('Error fetching Binance ticker:', error.response?.data || error.message);
      throw error;
    }
  }
}

module.exports = BinanceClient;
