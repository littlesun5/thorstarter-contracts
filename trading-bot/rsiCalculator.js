/**
 * RSI Calculator
 * Calculates RSI (Relative Strength Index) from price data
 */
class RSICalculator {
  constructor(period = 14) {
    this.period = period;
  }

  /**
   * Calculate RSI from an array of closing prices
   * @param {number[]} prices - Array of closing prices
   * @returns {number} RSI value (0-100)
   */
  calculate(prices) {
    if (prices.length < this.period + 1) {
      throw new Error(`Need at least ${this.period + 1} price points to calculate RSI`);
    }

    const changes = [];
    for (let i = 1; i < prices.length; i++) {
      changes.push(prices[i] - prices[i - 1]);
    }

    // Separate gains and losses
    const gains = changes.map(change => change > 0 ? change : 0);
    const losses = changes.map(change => change < 0 ? Math.abs(change) : 0);

    // Calculate initial average gain and loss
    let avgGain = gains.slice(0, this.period).reduce((sum, val) => sum + val, 0) / this.period;
    let avgLoss = losses.slice(0, this.period).reduce((sum, val) => sum + val, 0) / this.period;

    // Calculate smoothed averages for remaining periods
    for (let i = this.period; i < changes.length; i++) {
      avgGain = (avgGain * (this.period - 1) + gains[i]) / this.period;
      avgLoss = (avgLoss * (this.period - 1) + losses[i]) / this.period;
    }

    // Calculate RS and RSI
    if (avgLoss === 0) {
      return 100; // Avoid division by zero
    }

    const rs = avgGain / avgLoss;
    const rsi = 100 - (100 / (1 + rs));

    return rsi;
  }

  /**
   * Get RSI from klines data
   * @param {Array} klines - Array of kline objects with 'close' price
   * @returns {number} RSI value
   */
  calculateFromKlines(klines) {
    const closes = klines.map(k => parseFloat(k.close));
    return this.calculate(closes);
  }
}

module.exports = RSICalculator;
