#!/usr/bin/env node

/**
 * Backpack RSI bot with laddered scaling and dynamic exits.
 *
 * This script polls Backpack's public market data, computes 1-minute RSI, and
 * submits market orders via the REST API when thresholds are met. Orders are
 * signed with an ED25519 key pair following Backpack's instructions.
 */

const { TextEncoder } = require('util');
const nacl = require('tweetnacl');
const dotenv = require('dotenv');

dotenv.config();

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const encoder = new TextEncoder();

const DEFAULT_DCA_LEVELS = [
  { threshold: 150, size: 0.05 },
  { threshold: 250, size: 0.08 },
  { threshold: 500, size: 0.1 },
  { threshold: 800, size: 0.15 },
  { threshold: 1200, size: 0.2 },
  { threshold: 1500, size: 0.3 },
];

const logger = {
  info: (message, extra) => console.log(formatLog('INFO', message, extra)),
  warn: (message, extra) => console.warn(formatLog('WARN', message, extra)),
  error: (message, extra) => console.error(formatLog('ERROR', message, extra)),
};

function formatLog(level, message, extra) {
  const ts = new Date().toISOString();
  const suffix = extra ? ` | ${JSON.stringify(extra)}` : '';
  return `[${ts}] [${level}] ${message}${suffix}`;
}

function parseNumber(value, fallback) {
  if (value === undefined || value === null || value === '') {
    return fallback;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function buildConfig() {
  let dcaLevels = DEFAULT_DCA_LEVELS;
  if (process.env.DCA_LADDERS) {
    try {
      const parsed = JSON.parse(process.env.DCA_LADDERS);
      if (Array.isArray(parsed) && parsed.every((lvl) => lvl.threshold && lvl.size)) {
        dcaLevels = parsed.map((lvl) => ({
          threshold: Number(lvl.threshold),
          size: Number(lvl.size),
        }));
      } else {
        logger.warn('Invalid DCA_LADDERS format, falling back to defaults');
      }
    } catch (err) {
      logger.warn('Failed to parse DCA_LADDERS, using defaults', { error: err.message });
    }
  }

  const dryRun = (process.env.DRY_RUN ?? 'true').toLowerCase() !== 'false';

  return {
    symbol: process.env.BACKPACK_SYMBOL || 'BTC_USDC_PERP',
    interval: process.env.RSI_INTERVAL || '1m',
    rsiPeriod: parseNumber(process.env.RSI_PERIOD, 14),
    rsiOverbought: parseNumber(process.env.RSI_OVERBOUGHT, 71),
    rsiOversold: parseNumber(process.env.RSI_OVERSOLD, 29),
    baseOrderSize: parseNumber(process.env.BASE_ORDER_SIZE, 0.03),
    takerFee: parseNumber(process.env.TAKER_FEE, 0.0002),
    maxExposure: parseNumber(process.env.MAX_EXPOSURE_BTC, 2),
    stopLossUsd: parseNumber(process.env.MAX_LOSS_USD, 1000),
    pollIntervalMs: parseNumber(process.env.POLL_INTERVAL_MS, 15000),
    minOrderCooldownMs: parseNumber(process.env.ORDER_COOLDOWN_MS, 20000),
    lookbackMinutes: parseNumber(process.env.RSI_LOOKBACK_MINUTES, 180),
    positionRefreshMs: parseNumber(process.env.POSITION_REFRESH_MS, 5000),
    dcaLevels,
    dryRun,
    apiUrl: process.env.BACKPACK_API_URL || 'https://api.backpack.exchange',
    windowMs: parseNumber(process.env.BACKPACK_WINDOW_MS, 5000),
    quantityPrecision: parseNumber(process.env.QUANTITY_PRECISION, 5),
  };
}

class BackpackClient {
  constructor({ apiKey, secret, apiUrl, windowMs, dryRun }) {
    this.apiUrl = apiUrl.endsWith('/') ? apiUrl.slice(0, -1) : apiUrl;
    this.windowMs = windowMs;
    this.dryRun = dryRun;
    this.hasAuth = Boolean(apiKey && secret);
    if (secret) {
      const seed = Buffer.from(secret, 'base64');
      if (seed.length !== 32) {
        throw new Error('BACKPACK_SECRET must be a base64-encoded 32-byte seed');
      }
      const keyPair = nacl.sign.keyPair.fromSeed(seed);
      this.secretKey = keyPair.secretKey;
      this.derivedApiKey = Buffer.from(keyPair.publicKey).toString('base64');
    }
    this.apiKey = apiKey || this.derivedApiKey;
    if (this.hasAuth && !this.apiKey) {
      throw new Error('Unable to derive API key from secret; please set BACKPACK_API_KEY');
    }
    if (!this.hasAuth) {
      logger.warn('Backpack API credentials missing. Observation mode only.');
    }
  }

  async getKlines(params) {
    return this.request('GET', '/api/v1/klines', { params });
  }

  async getTicker(symbol) {
    return this.request('GET', '/api/v1/ticker', { params: { symbol } });
  }

  async getPositions(symbol) {
    if (!this.hasAuth) {
      throw new Error('Cannot fetch positions without API credentials');
    }
    const params = {};
    if (symbol) params.symbol = symbol;
    return this.request('GET', '/api/v1/position', {
      params,
      instruction: 'positionQuery',
    });
  }

  async createOrder(payload) {
    return this.request('POST', '/api/v1/order', {
      body: payload,
      instruction: 'orderExecute',
    });
  }

  async request(method, path, options = {}) {
    const { params, body, instruction } = options;
    const url = new URL(`${this.apiUrl}${path}`);
    if (params) {
      Object.entries(params)
        .filter(([, value]) => value !== undefined && value !== null)
        .forEach(([key, value]) => url.searchParams.append(key, value));
    }

    const headers = {
      'Content-Type': 'application/json',
    };
    let requestBody;
    if (body) {
      requestBody = JSON.stringify(body);
    }

    if (instruction) {
      if (!this.hasAuth) {
        throw new Error('Signed request attempted without credentials');
      }
      const timestamp = Date.now();
      const window = this.windowMs;
      const payloadToSign =
        method === 'GET'
          ? Object.fromEntries(url.searchParams.entries())
          : body || {};
      const signingString = this.buildSigningString(instruction, payloadToSign, timestamp, window);
      const signature = this.sign(signingString);
      headers['X-API-KEY'] = this.apiKey;
      headers['X-SIGNATURE'] = signature;
      headers['X-TIMESTAMP'] = String(timestamp);
      headers['X-WINDOW'] = String(window);
    }

    const response = await fetch(url, {
      method,
      headers,
      body: requestBody,
    });

    const text = await response.text();
    const payload = text ? safeJsonParse(text) : null;

    if (!response.ok) {
      const message = payload?.message || payload?.error || text || 'Unknown error';
      throw new Error(`Backpack API error ${response.status}: ${message}`);
    }

    return payload;
  }

  buildSigningString(instruction, payload, timestamp, window) {
    const components = [`instruction=${instruction}`];
    const paramsString = this.stringifyPayload(payload);
    if (paramsString) {
      components.push(paramsString);
    }
    components.push(`timestamp=${timestamp}`);
    components.push(`window=${window}`);
    return components.join('&');
  }

  stringifyPayload(payload) {
    if (!payload || Object.keys(payload).length === 0) {
      return '';
    }
    const entries = Object.entries(payload)
      .filter(([, value]) => value !== undefined && value !== null)
      .map(([key, value]) => [key, Array.isArray(value) ? JSON.stringify(value) : String(value)]);
    entries.sort(([a], [b]) => a.localeCompare(b));
    return entries
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
      .join('&');
  }

  sign(message) {
    if (!this.secretKey) {
      throw new Error('Cannot sign without secret key');
    }
    const bytes = encoder.encode(message);
    const signature = nacl.sign.detached(bytes, this.secretKey);
    return Buffer.from(signature).toString('base64');
  }
}

class RsiCalculator {
  constructor(period) {
    this.period = period;
    this.prevClose = null;
    this.avgGain = null;
    this.avgLoss = null;
    this.seedBuffer = [];
  }

  update(price) {
    if (this.prevClose === null) {
      this.prevClose = price;
      return null;
    }
    const delta = price - this.prevClose;
    const gain = delta > 0 ? delta : 0;
    const loss = delta < 0 ? -delta : 0;

    if (this.avgGain === null || this.avgLoss === null) {
      this.seedBuffer.push({ gain, loss });
      if (this.seedBuffer.length === this.period) {
        const totalGain = this.seedBuffer.reduce((sum, point) => sum + point.gain, 0);
        const totalLoss = this.seedBuffer.reduce((sum, point) => sum + point.loss, 0);
        this.avgGain = totalGain / this.period;
        this.avgLoss = totalLoss / this.period;
        this.seedBuffer = [];
      }
      this.prevClose = price;
      return null;
    }

    this.avgGain = ((this.avgGain * (this.period - 1)) + gain) / this.period;
    this.avgLoss = ((this.avgLoss * (this.period - 1)) + loss) / this.period;
    this.prevClose = price;

    if (this.avgLoss === 0) {
      return 100;
    }
    const rs = this.avgGain / this.avgLoss;
    return 100 - 100 / (1 + rs);
  }
}

class RsiBot {
  constructor(config, client) {
    this.config = config;
    this.client = client;
    this.rsi = new RsiCalculator(config.rsiPeriod);
    this.state = {
      lastProcessedBar: null,
      lastOrderMs: 0,
      anchorPrice: null,
      anchorDirection: null,
      dcaTriggered: new Set(),
      latestPrice: null,
    };
    this.position = {
      qty: 0,
      entryPrice: null,
      pnl: 0,
    };
    this.lastPositionRefresh = 0;
    this.observationMode = !this.client.hasAuth;
    if (this.config.dryRun) {
      logger.info('Bot running in DRY-RUN mode. Orders will be logged only.');
    }
    if (this.observationMode) {
      logger.warn('Observation-only mode. Positions and orders are disabled.');
    }
  }

  async start() {
    logger.info('Initializing RSI bot', {
      symbol: this.config.symbol,
      interval: this.config.interval,
      dryRun: this.config.dryRun,
    });
    await this.seedRsi();
    await this.refreshPosition(true);
    while (true) {
      try {
        await this.tick();
      } catch (err) {
        logger.error('Tick error', { error: err.message });
      }
      await sleep(this.config.pollIntervalMs);
    }
  }

  async seedRsi() {
    const now = Math.floor(Date.now() / 1000);
    const startTime = now - this.config.lookbackMinutes * 60;
    logger.info('Seeding RSI calculator', { lookbackMinutes: this.config.lookbackMinutes });
    const candles = await this.client.getKlines({
      symbol: this.config.symbol,
      interval: this.config.interval,
      startTime,
      endTime: now,
    });
    if (!Array.isArray(candles) || candles.length === 0) {
      throw new Error('Failed to load initial candles');
    }
    candles.forEach((bar) => {
      const close = parseFloat(bar.close);
      if (Number.isFinite(close)) {
        this.state.latestPrice = close;
        this.rsi.update(close);
        this.state.lastProcessedBar = toTimestamp(bar.end);
      }
    });
    logger.info('RSI seeded', { processedCandles: candles.length });
  }

  async tick() {
    await this.consumeNewCandles();
    if (!this.observationMode) {
      await this.refreshPosition();
      if (this.client.hasAuth) {
        await this.maybeScalePosition();
        await this.checkExitConditions();
      }
    }
  }

  async consumeNewCandles() {
    const now = Math.floor(Date.now() / 1000);
    const startTime = now - 180; // fetch the last three minutes to avoid gaps
    const candles = await this.client.getKlines({
      symbol: this.config.symbol,
      interval: this.config.interval,
      startTime,
      endTime: now,
    });
    for (const bar of candles) {
      const barTime = toTimestamp(bar.end);
      if (this.state.lastProcessedBar && barTime <= this.state.lastProcessedBar) {
        continue;
      }
      const close = parseFloat(bar.close);
      if (!Number.isFinite(close)) {
        continue;
      }
      this.state.latestPrice = close;
      this.state.lastProcessedBar = barTime;
      const rsiValue = this.rsi.update(close);
      if (rsiValue !== null) {
        logger.info('RSI update', { price: close, rsi: Number(rsiValue.toFixed(2)) });
        await this.evaluateSignal(rsiValue, close);
      }
    }
  }

  async evaluateSignal(rsiValue, price) {
    if (this.observationMode) {
      this.logObservation(rsiValue, price);
      return;
    }

    if (!this.client.hasAuth) {
      return;
    }

    const positionQty = this.position.qty;

    if (Math.abs(positionQty) < 1e-6) {
      if (rsiValue >= this.config.rsiOverbought) {
        await this.tryEnter('short', price, 'RSI overbought');
      } else if (rsiValue <= this.config.rsiOversold) {
        await this.tryEnter('long', price, 'RSI oversold');
      }
    } else {
      // Ensure anchor tracking stays in sync with externally opened positions.
      if (!this.state.anchorPrice) {
        this.state.anchorPrice = this.position.entryPrice || price;
        this.state.anchorDirection = positionQty > 0 ? 'long' : 'short';
      }
    }
  }

  logObservation(rsiValue, price) {
    if (rsiValue >= this.config.rsiOverbought) {
      logger.info('Observation: short signal detected', { price, rsi: Number(rsiValue.toFixed(2)) });
    } else if (rsiValue <= this.config.rsiOversold) {
      logger.info('Observation: long signal detected', { price, rsi: Number(rsiValue.toFixed(2)) });
    }
  }

  async tryEnter(direction, price, reason) {
    if (this.config.dryRun) {
      logger.info('DRY-RUN entry skipped', { direction, price, reason });
      this.state.lastOrderMs = Date.now();
      return;
    }

    if (this.cooldownActive()) {
      logger.warn('Entry blocked by cooldown', { direction, reason });
      return;
    }

    const currentQty = this.position.qty || 0;
    if (Math.abs(currentQty) > 1e-6) {
      logger.warn('Cannot enter new base position while existing exposure is active', {
        direction,
        currentQty,
      });
      return;
    }

    const projectedQty = direction === 'long' ? this.config.baseOrderSize : -this.config.baseOrderSize;
    if (Math.abs(projectedQty) > this.config.maxExposure) {
      logger.warn('Entry size exceeds max exposure', { direction, projectedQty });
      return;
    }

    const side = direction === 'long' ? 'Bid' : 'Ask';
    const placed = await this.submitOrder({
      side,
      quantity: this.config.baseOrderSize,
      reduceOnly: false,
      label: reason,
    });
    if (placed) {
      this.state.anchorPrice = price;
      this.state.anchorDirection = direction;
      this.state.dcaTriggered.clear();
    }
  }

  async maybeScalePosition() {
    if (!this.state.anchorPrice || !this.state.anchorDirection) {
      return;
    }
    if (Math.abs(this.position.qty) < 1e-6) {
      return;
    }
    const adverseMove = this.computeAdverseMove();
    if (adverseMove <= 0) {
      return;
    }
    for (let i = 0; i < this.config.dcaLevels.length; i += 1) {
      const level = this.config.dcaLevels[i];
      if (this.state.dcaTriggered.has(i)) {
        continue;
      }
      if (adverseMove >= level.threshold) {
        const direction = this.state.anchorDirection;
        const projectedQty =
          this.position.qty + (direction === 'long' ? level.size : -level.size);
        if (Math.abs(projectedQty) > this.config.maxExposure) {
          logger.warn('Skipping DCA level: max exposure reached', {
            level: level.threshold,
            projectedQty,
          });
          this.state.dcaTriggered.add(i);
          continue;
        }
        const side = direction === 'long' ? 'Bid' : 'Ask';
        const success = await this.submitOrder({
          side,
          quantity: level.size,
          reduceOnly: false,
          label: `DCA ${level.threshold}`,
        });
        if (success) {
          this.state.dcaTriggered.add(i);
        }
      }
    }
  }

  computeAdverseMove() {
    if (!this.state.latestPrice || !this.state.anchorPrice) {
      return 0;
    }
    if (this.state.anchorDirection === 'long') {
      return this.state.anchorPrice - this.state.latestPrice;
    }
    return this.state.latestPrice - this.state.anchorPrice;
  }

  async checkExitConditions() {
    if (Math.abs(this.position.qty) < 1e-6) {
      return;
    }
    if (!this.state.latestPrice || !this.position.entryPrice) {
      return;
    }
    const qty = this.position.qty;
    const entry = this.position.entryPrice;
    const price = this.state.latestPrice;
    const pnl = (price - entry) * qty;
    const requiredProfit =
      Math.abs(entry * qty) * this.config.takerFee * 2;

    if (pnl >= requiredProfit && pnl > 0) {
      logger.info('Closing position: fees covered', { pnl, requiredProfit });
      await this.closePosition('fee-covered');
      return;
    }
    if (-pnl >= this.config.stopLossUsd) {
      logger.warn('Closing position: stop loss hit', { pnl });
      await this.closePosition('max-loss', true);
    }
  }

  async closePosition(reason, force = false) {
    if (Math.abs(this.position.qty) < 1e-6) {
      return;
    }
    const side = this.position.qty > 0 ? 'Ask' : 'Bid';
    const quantity = Math.abs(this.position.qty);
    await this.submitOrder({
      side,
      quantity,
      reduceOnly: true,
      label: `Exit - ${reason}`,
      force,
    });
    this.resetAnchor();
  }

  async submitOrder({ side, quantity, reduceOnly, label, force = false }) {
    const now = Date.now();
    if (!force && this.cooldownActive()) {
      logger.warn('Order blocked by cooldown', { side, label });
      return false;
    }

    if (this.config.dryRun) {
      logger.info('DRY-RUN order', { side, quantity, label, reduceOnly });
      this.state.lastOrderMs = now;
      return true;
    }

    const payload = {
      symbol: this.config.symbol,
      side,
      orderType: 'Market',
      quantity: formatQuantity(quantity, this.config.quantityPrecision),
      timeInForce: 'IOC',
    };
    if (reduceOnly) {
      payload.reduceOnly = true;
    }

    try {
      const result = await this.client.createOrder(payload);
      this.state.lastOrderMs = now;
      logger.info('Order submitted', { label, side, quantity, reduceOnly, orderId: result?.id });
      await this.refreshPosition(true);
      return true;
    } catch (err) {
      logger.error('Order submission failed', { error: err.message, label });
      return false;
    }
  }

  cooldownActive() {
    const elapsed = Date.now() - this.state.lastOrderMs;
    return elapsed < this.config.minOrderCooldownMs;
  }

  async refreshPosition(force = false) {
    if (!this.client.hasAuth) {
      return;
    }
    const now = Date.now();
    if (!force && now - this.lastPositionRefresh < this.config.positionRefreshMs) {
      return;
    }
    this.lastPositionRefresh = now;
    try {
      const response = await this.client.getPositions(this.config.symbol);
      const positionRecord = Array.isArray(response)
        ? response.find((row) => row.symbol === this.config.symbol)
        : Array.isArray(response?.positions)
          ? response.positions.find((row) => row.symbol === this.config.symbol)
          : null;
      if (!positionRecord) {
        if (Math.abs(this.position.qty) > 1e-6) {
          this.position = { qty: 0, entryPrice: null, pnl: 0 };
          this.resetAnchor();
        }
        return;
      }
      const qty = parseFloat(positionRecord.netQuantity);
      const entryPrice = parseFloat(positionRecord.entryPrice);
      const pnl = parseFloat(positionRecord.pnlUnrealized || '0');
      this.position = {
        qty: Number.isFinite(qty) ? qty : 0,
        entryPrice: Number.isFinite(entryPrice) ? entryPrice : null,
        pnl: Number.isFinite(pnl) ? pnl : 0,
      };
      if (Math.abs(this.position.qty) < 1e-6) {
        this.resetAnchor();
      } else if (!this.state.anchorPrice) {
        this.state.anchorPrice = this.position.entryPrice;
        this.state.anchorDirection = this.position.qty > 0 ? 'long' : 'short';
      }
    } catch (err) {
      logger.error('Failed to refresh position', { error: err.message });
    }
  }

  resetAnchor() {
    this.state.anchorPrice = null;
    this.state.anchorDirection = null;
    this.state.dcaTriggered.clear();
  }
}

function toTimestamp(dateString) {
  if (!dateString) {
    return null;
  }
  // Backpack returns "YYYY-MM-DD HH:mm:ss" in UTC.
  const iso = dateString.replace(' ', 'T') + 'Z';
  const value = Date.parse(iso);
  return Number.isFinite(value) ? value : null;
}

function safeJsonParse(text) {
  try {
    return JSON.parse(text);
  } catch (err) {
    logger.error('Failed to parse JSON response', { error: err.message, payload: text });
    return null;
  }
}

function formatQuantity(value, precision = 5) {
  return Number(value).toFixed(precision).replace(/\.?0+$/, '');
}

async function main() {
  const config = buildConfig();
  const apiKey = process.env.BACKPACK_API_KEY;
  const secret = process.env.BACKPACK_SECRET;

  if (!config.dryRun && (!apiKey || !secret)) {
    throw new Error('Live trading requires BACKPACK_API_KEY and BACKPACK_SECRET');
  }

  const client = new BackpackClient({
    apiKey,
    secret,
    apiUrl: config.apiUrl,
    windowMs: config.windowMs,
    dryRun: config.dryRun,
  });

  const bot = new RsiBot(config, client);
  await bot.start();
}

main().catch((err) => {
  logger.error('Fatal bot error', { error: err.stack || err.message });
  process.exit(1);
});

process.on('SIGINT', () => {
  logger.warn('Caught SIGINT, shutting down.');
  process.exit(0);
});

