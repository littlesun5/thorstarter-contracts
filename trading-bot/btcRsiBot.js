const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });
const BackpackClient = require('./backpackClient');
const BinanceClient = require('./binanceClient');
const RSICalculator = require('./rsiCalculator');

class BTCRSIBot {
  constructor() {
    // Initialize clients
    this.backpack = new BackpackClient(
      process.env.BACKPACK_API_KEY,
      process.env.BACKPACK_API_SECRET
    );
    this.binance = new BinanceClient();
    this.rsiCalculator = new RSICalculator(14);

    // Configuration
    this.symbol = 'BTC_USDC';
    this.binanceSymbol = 'BTCUSDT';
    this.initialOrderSize = 0.03; // BTC
    this.maxPosition = 2.0; // BTC
    this.stopLossUSD = 1000; // USD
    this.marketFeeRate = 0.0002; // 0.02%
    this.limitFeeRate = 0; // 0%

    // RSI thresholds
    this.rsiShortThreshold = 71;
    this.rsiLongThreshold = 29;

    // Scaling order configuration
    this.scalingLevels = [
      { lossUSD: 150, size: 0.05 },
      { lossUSD: 250, size: 0.08 },
      { lossUSD: 500, size: 0.10 },
      { lossUSD: 800, size: 0.15 },
      { lossUSD: 1200, size: 0.20 },
      { lossUSD: 1500, size: 0.30 }
    ];

    // State
    this.currentPosition = null;
    this.lastOrderTime = 0;
    this.minOrderInterval = 20000; // 20 seconds in milliseconds
    this.scalingOrdersPlaced = [];
    this.isRunning = false;
  }

  /**
   * Get price data from Backpack or Binance
   */
  async getPriceData() {
    try {
      // Try Backpack first
      const klines = await this.backpack.getKlines(this.symbol, '1m', 100);
      if (klines && klines.length > 0) {
        return klines;
      }
    } catch (error) {
      console.log('Backpack data unavailable, using Binance...');
    }

    // Fallback to Binance
    try {
      const klines = await this.binance.getKlines(this.binanceSymbol, '1m', 100);
      return klines;
    } catch (error) {
      console.error('Failed to fetch price data from both sources');
      throw error;
    }
  }

  /**
   * Calculate current RSI
   */
  async getCurrentRSI() {
    const klines = await this.getPriceData();
    return this.rsiCalculator.calculateFromKlines(klines);
  }

  /**
   * Get current position
   */
  async updatePosition() {
    try {
      const positions = await this.backpack.getPositions();
      const btcPosition = positions.find(p => p.symbol === this.symbol);
      
      if (btcPosition && parseFloat(btcPosition.size) !== 0) {
        this.currentPosition = {
          symbol: btcPosition.symbol,
          size: parseFloat(btcPosition.size),
          entryPrice: parseFloat(btcPosition.entryPrice),
          markPrice: parseFloat(btcPosition.markPrice),
          unrealizedPnl: parseFloat(btcPosition.unrealizedPnl),
          side: parseFloat(btcPosition.size) > 0 ? 'long' : 'short'
        };
      } else {
        this.currentPosition = null;
        this.scalingOrdersPlaced = [];
      }
    } catch (error) {
      console.error('Error updating position:', error.message);
    }
  }

  /**
   * Get current BTC price
   */
  async getCurrentPrice() {
    try {
      const ticker = await this.backpack.getTicker(this.symbol);
      // Backpack API may return different formats, try common fields
      return parseFloat(ticker.lastPrice || ticker.price || ticker.close || ticker.last);
    } catch (error) {
      try {
        const ticker = await this.binance.getTicker(this.binanceSymbol);
        return ticker.price;
      } catch (err) {
        console.error('Failed to get current price');
        throw err;
      }
    }
  }

  /**
   * Check if enough time has passed since last order
   */
  canPlaceOrder() {
    const now = Date.now();
    if (now - this.lastOrderTime < this.minOrderInterval) {
      return false;
    }
    return true;
  }

  /**
   * Calculate total position size
   */
  getTotalPositionSize() {
    if (!this.currentPosition) return 0;
    return Math.abs(this.currentPosition.size);
  }

  /**
   * Place an order with rate limiting
   */
  async placeOrderWithLimit(side, orderType, quantity, price = null) {
    if (!this.canPlaceOrder()) {
      console.log('Order rate limit: waiting...');
      return null;
    }

    if (this.getTotalPositionSize() + quantity > this.maxPosition) {
      console.log(`Cannot place order: would exceed max position of ${this.maxPosition} BTC`);
      return null;
    }

    try {
      const result = await this.backpack.placeOrder(
        this.symbol,
        side,
        orderType,
        quantity,
        price
      );
      this.lastOrderTime = Date.now();
      console.log(`Order placed: ${side} ${quantity} BTC @ ${orderType} ${price || 'market'}`);
      return result;
    } catch (error) {
      console.error('Error placing order:', error.message);
      return null;
    }
  }

  /**
   * Calculate fees for an order
   */
  calculateFees(quantity, price, isMarket) {
    const orderValue = quantity * price;
    const feeRate = isMarket ? this.marketFeeRate : this.limitFeeRate;
    return orderValue * feeRate;
  }

  /**
   * Check if profit covers fees
   */
  async checkProfitCoversFees() {
    if (!this.currentPosition) return false;

    await this.updatePosition();
    if (!this.currentPosition) return false;

    const position = this.currentPosition;
    const currentPrice = await this.getCurrentPrice();
    const positionValue = Math.abs(position.size) * currentPrice;

    // Calculate total fees paid (entry + exit)
    const entryFees = this.calculateFees(Math.abs(position.size), position.entryPrice, false);
    const exitFees = this.calculateFees(Math.abs(position.size), currentPrice, true);
    const totalFees = entryFees + exitFees;

    // Check if unrealized PnL covers fees
    const profitAfterFees = position.unrealizedPnl - totalFees;
    
    return profitAfterFees > 0;
  }

  /**
   * Check stop loss
   */
  async checkStopLoss() {
    if (!this.currentPosition) return false;

    await this.updatePosition();
    if (!this.currentPosition) return false;

    const unrealizedLoss = Math.abs(this.currentPosition.unrealizedPnl);
    return unrealizedLoss >= this.stopLossUSD;
  }

  /**
   * Calculate loss in USD from entry price
   */
  calculateLossFromEntry() {
    if (!this.currentPosition) return 0;

    const position = this.currentPosition;
    const loss = Math.abs(position.unrealizedPnl);
    
    // For short positions, unrealizedPnl is negative when price goes up (loss)
    // For long positions, unrealizedPnl is negative when price goes down (loss)
    if (position.unrealizedPnl < 0) {
      return loss;
    }
    return 0;
  }

  /**
   * Check if scaling order should be placed
   */
  async checkScalingOrders() {
    if (!this.currentPosition) return;

    await this.updatePosition();
    if (!this.currentPosition) return;

    const loss = this.calculateLossFromEntry();
    if (loss <= 0) return; // Not losing, no scaling needed

    // Check if RSI continues in the same direction
    const rsi = await this.getCurrentRSI();
    const shouldScale = 
      (this.currentPosition.side === 'short' && rsi > this.rsiShortThreshold) ||
      (this.currentPosition.side === 'long' && rsi < this.rsiLongThreshold);

    if (!shouldScale) return;

    // Find all scaling levels that should be triggered
    for (const level of this.scalingLevels) {
      if (loss >= level.lossUSD && !this.scalingOrdersPlaced.includes(level.lossUSD)) {
        // Check if adding this order would exceed max position
        const newTotalSize = this.getTotalPositionSize() + level.size;
        if (newTotalSize > this.maxPosition) {
          console.log(`Scaling order skipped at $${level.lossUSD}: would exceed max position`);
          this.scalingOrdersPlaced.push(level.lossUSD); // Mark as attempted to avoid retrying
          continue;
        }

        // Place scaling order in the same direction
        const side = this.currentPosition.side === 'long' ? 'Bid' : 'Ask';
        const currentPrice = await this.getCurrentPrice();
        const result = await this.placeOrderWithLimit(side, 'Limit', level.size, currentPrice);
        
        if (result) {
          this.scalingOrdersPlaced.push(level.lossUSD);
          console.log(`Scaling order placed at loss level $${level.lossUSD}: ${level.size} BTC @ $${currentPrice.toFixed(2)}`);
        } else {
          // If order failed, don't mark as placed so we can retry
          console.log(`Failed to place scaling order at $${level.lossUSD}, will retry`);
        }
        // Don't break - continue to check all levels that should be triggered
      }
    }
  }

  /**
   * Close position if profit covers fees
   */
  async closePositionIfProfitable() {
    if (await this.checkProfitCoversFees()) {
      console.log('Profit covers fees, closing position...');
      try {
        await this.backpack.closePosition(this.symbol, 'Market');
        this.currentPosition = null;
        this.scalingOrdersPlaced = [];
        console.log('Position closed successfully');
      } catch (error) {
        console.error('Error closing position:', error.message);
      }
    }
  }

  /**
   * Check stop loss and close if needed
   */
  async checkAndExecuteStopLoss() {
    if (await this.checkStopLoss()) {
      console.log(`Stop loss triggered! Loss: $${Math.abs(this.currentPosition.unrealizedPnl)}`);
      try {
        await this.backpack.closePosition(this.symbol, 'Market');
        this.currentPosition = null;
        this.scalingOrdersPlaced = [];
        console.log('Position closed due to stop loss');
      } catch (error) {
        console.error('Error executing stop loss:', error.message);
      }
    }
  }

  /**
   * Open new position based on RSI
   */
  async openPositionBasedOnRSI(rsi) {
    if (this.currentPosition) {
      return; // Already have a position
    }

    const currentPrice = await this.getCurrentPrice();
    
    if (rsi > this.rsiShortThreshold) {
      // RSI is high, open short position
      console.log(`RSI ${rsi.toFixed(2)} > ${this.rsiShortThreshold}, opening short position...`);
      await this.placeOrderWithLimit('Ask', 'Limit', this.initialOrderSize, currentPrice);
    } else if (rsi < this.rsiLongThreshold) {
      // RSI is low, open long position
      console.log(`RSI ${rsi.toFixed(2)} < ${this.rsiLongThreshold}, opening long position...`);
      await this.placeOrderWithLimit('Bid', 'Limit', this.initialOrderSize, currentPrice);
    }
  }

  /**
   * Main trading loop
   */
  async run() {
    if (this.isRunning) {
      console.log('Bot is already running');
      return;
    }

    this.isRunning = true;
    console.log('BTC RSI Trading Bot started...');
    console.log(`RSI Short Threshold: ${this.rsiShortThreshold}`);
    console.log(`RSI Long Threshold: ${this.rsiLongThreshold}`);
    console.log(`Initial Order Size: ${this.initialOrderSize} BTC`);
    console.log(`Max Position: ${this.maxPosition} BTC`);
    console.log(`Stop Loss: $${this.stopLossUSD}`);

    while (this.isRunning) {
      try {
        // Update current position
        await this.updatePosition();

        // Get current RSI
        const rsi = await this.getCurrentRSI();
        console.log(`\n[${new Date().toISOString()}] Current RSI: ${rsi.toFixed(2)}`);

        if (this.currentPosition) {
          // We have an open position
          console.log(`Position: ${this.currentPosition.side} ${Math.abs(this.currentPosition.size)} BTC`);
          console.log(`Entry Price: $${this.currentPosition.entryPrice.toFixed(2)}`);
          console.log(`Mark Price: $${this.currentPosition.markPrice.toFixed(2)}`);
          console.log(`Unrealized PnL: $${this.currentPosition.unrealizedPnl.toFixed(2)}`);

          // Check stop loss first
          await this.checkAndExecuteStopLoss();
          
          // If still have position, check profit
          if (this.currentPosition) {
            await this.closePositionIfProfitable();
          }

          // If still have position, check scaling orders
          if (this.currentPosition) {
            await this.checkScalingOrders();
          }
        } else {
          // No position, check if we should open one
          await this.openPositionBasedOnRSI(rsi);
        }

        // Wait 1 minute before next check
        await this.sleep(60000);
      } catch (error) {
        console.error('Error in trading loop:', error.message);
        await this.sleep(10000); // Wait 10 seconds on error
      }
    }
  }

  /**
   * Stop the bot
   */
  stop() {
    console.log('Stopping bot...');
    this.isRunning = false;
  }

  /**
   * Sleep utility
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Run the bot if this file is executed directly
if (require.main === module) {
  const bot = new BTCRSIBot();
  
  // Handle graceful shutdown
  process.on('SIGINT', () => {
    console.log('\nReceived SIGINT, shutting down gracefully...');
    bot.stop();
    process.exit(0);
  });

  process.on('SIGTERM', () => {
    console.log('\nReceived SIGTERM, shutting down gracefully...');
    bot.stop();
    process.exit(0);
  });

  bot.run().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

module.exports = BTCRSIBot;
