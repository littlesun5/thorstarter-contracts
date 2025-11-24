const axios = require('axios');
const crypto = require('crypto');

class BackpackClient {
  constructor(apiKey, apiSecret) {
    this.apiKey = apiKey;
    this.apiSecret = apiSecret;
    this.baseURL = 'https://api.backpack.exchange';
  }

  /**
   * Sign a request according to Backpack API requirements
   */
  signRequest(method, path, body = null, timestamp = null) {
    if (!timestamp) {
      timestamp = Date.now();
    }

    const bodyString = body ? JSON.stringify(body) : '';
    const message = `${timestamp}${method}${path}${bodyString}`;
    
    const signature = crypto
      .createHmac('sha256', this.apiSecret)
      .update(message)
      .digest('hex');

    return {
      signature,
      timestamp: timestamp.toString()
    };
  }

  /**
   * Make an authenticated request to Backpack API
   */
  async authenticatedRequest(method, path, body = null) {
    const { signature, timestamp } = this.signRequest(method, path, body);

    const config = {
      method,
      url: `${this.baseURL}${path}`,
      headers: {
        'X-API-Key': this.apiKey,
        'X-Timestamp': timestamp,
        'X-Signature': signature,
        'Content-Type': 'application/json'
      }
    };

    if (body) {
      config.data = body;
    }

    try {
      const response = await axios(config);
      return response.data;
    } catch (error) {
      console.error(`API Error: ${method} ${path}`, error.response?.data || error.message);
      throw error;
    }
  }

  /**
   * Get current ticker price
   */
  async getTicker(symbol = 'BTC_USDC') {
    try {
      const response = await axios.get(`${this.baseURL}/api/v1/ticker`, {
        params: { symbol }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching ticker:', error.response?.data || error.message);
      throw error;
    }
  }

  /**
   * Get klines (candlestick data) for RSI calculation
   */
  async getKlines(symbol = 'BTC_USDC', interval = '1m', limit = 100) {
    try {
      const response = await axios.get(`${this.baseURL}/api/v1/klines`, {
        params: { symbol, interval, limit }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching klines:', error.response?.data || error.message);
      throw error;
    }
  }

  /**
   * Get account balance
   */
  async getBalance() {
    return this.authenticatedRequest('GET', '/api/v1/capital');
  }

  /**
   * Get open positions
   */
  async getPositions() {
    return this.authenticatedRequest('GET', '/api/v1/positions');
  }

  /**
   * Place an order
   * @param {string} symbol - Trading pair (e.g., 'BTC_USDC')
   * @param {string} side - 'Bid' for buy/long, 'Ask' for sell/short
   * @param {string} orderType - 'Limit' or 'Market'
   * @param {number} quantity - Order quantity
   * @param {number} price - Limit price (required for Limit orders)
   */
  async placeOrder(symbol, side, orderType, quantity, price = null) {
    const body = {
      symbol,
      side,
      orderType,
      quantity: quantity.toString()
    };

    if (orderType === 'Limit' && price) {
      body.price = price.toString();
    }

    return this.authenticatedRequest('POST', '/api/v1/order', body);
  }

  /**
   * Cancel an order
   */
  async cancelOrder(symbol, orderId) {
    const body = {
      symbol,
      orderId
    };
    return this.authenticatedRequest('DELETE', '/api/v1/order', body);
  }

  /**
   * Cancel all orders for a symbol
   */
  async cancelAllOrders(symbol) {
    const body = { symbol };
    return this.authenticatedRequest('DELETE', '/api/v1/orders', body);
  }

  /**
   * Close a position
   */
  async closePosition(symbol, orderType = 'Market') {
    const positions = await this.getPositions();
    const position = positions.find(p => p.symbol === symbol);
    
    if (!position || parseFloat(position.size) === 0) {
      return { message: 'No position to close' };
    }

    const side = parseFloat(position.size) > 0 ? 'Ask' : 'Bid';
    const quantity = Math.abs(parseFloat(position.size));

    return this.placeOrder(symbol, side, orderType, quantity);
  }
}

module.exports = BackpackClient;
