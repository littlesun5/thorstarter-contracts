#!/usr/bin/env node

/**
 * Backpack Exchange BTC RSI strategy bot.
 *
 * Strategy summary:
 * - Pulls 1 minute BTC/USDT closes from Binance to compute RSI.
 * - Opens a 0.03 BTC short when RSI > 71, or a 0.03 BTC long when RSI < 29.
 * - Adds scaling orders as the market moves against the position according to the configured ladder.
 * - Closes the position once unrealized PnL covers estimated taker fees, or if unrealized loss exceeds $1k.
 * - Respects a minimum 20 second delay between order placements and caps exposure at 2 BTC.
 *
 * IMPORTANT: Provide API credentials and overrides via environment variables (.env).
 */

require('dotenv').config();
const fetch = require('node-fetch');
const nacl = require('tweetnacl');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const DEFAULT_SCALE_PLAN = [
  { threshold: 150, quantity: 0.05 },
  { threshold: 250, quantity: 0.08 },
  { threshold: 500, quantity: 0.1 },
  { threshold: 800, quantity: 0.15 },
  { threshold: 1200, quantity: 0.2 },
  { threshold: 1500, quantity: 0.3 },
];

const CONFIG = {
  apiKey: process.env.BACKPACK_API_KEY,
  apiSecret: process.env.BACKPACK_API_SECRET,
  backpackBaseUrl: process.env.BACKPACK_BASE_URL || 'https://api.backpack.exchange',
  backpackWindow: parseInt(process.env.BACKPACK_WINDOW || '5000', 10),
  symbol: process.env.BACKPACK_SYMBOL || 'BTC_USDC_PERP',
  binanceSymbol: process.env.BINANCE_SYMBOL || 'BTCUSDT',
  baseOrderSize: parseFloat(process.env.BASE_ORDER_SIZE || '0.03'),
  maxPositionSize: parseFloat(process.env.MAX_POSITION_SIZE || '2'),
  maxDrawdownUsd: parseFloat(process.env.MAX_DRAWDOWN_USD || '1000'),
  minOrderSize: parseFloat(process.env.MIN_ORDER_SIZE || '0.001'),
  takerFee: parseFloat(process.env.TAKER_FEE || '0.0002'),
  pollIntervalMs: parseInt(process.env.POLL_INTERVAL_MS || '15000', 10),
  orderCooldownMs: parseInt(process.env.ORDER_COOLDOWN_MS || '20000', 10),
  rsiPeriod: parseInt(process.env.RSI_PERIOD || '14', 10),
  rsiOverbought: parseFloat(process.env.RSI_OVERBOUGHT || '71'),
  rsiOversold: parseFloat(process.env.RSI_OVERSOLD || '29'),
  scalePlan: parseScalePlan(process.env.SCALE_PLAN),
};

guardConfig();

const signingKey = nacl.sign.keyPair.fromSeed(Buffer.from(CONFIG.apiSecret, 'base64')).secretKey;

const state = {
  lastRsiZone: 'neutral',
  lastOrderMs: 0,
  activeBias: null,
};

process.on('SIGINT', () => {
  console.log('\n[EXIT] Caught interrupt signal. Shutting down gracefully.');
  process.exit(0);
});

process.on('unhandledRejection', (err) => {
  console.error('[ERROR] Unhandled rejection:', err);
});

async function main() {
  console.log(`[INIT] Starting RSI bot for ${CONFIG.symbol} using Binance ${CONFIG.binanceSymbol}`);
  while (true) {
    const loopStarted = Date.now();
    try {
      await runTick();
    } catch (err) {
      console.error('[TICK ERROR]', err?.message || err);
    }
    const elapsed = Date.now() - loopStarted;
    await sleep(Math.max(0, CONFIG.pollIntervalMs - elapsed));
  }
}

async function runTick() {
  const market = await fetchBinanceMarket();
  if (!market) {
    console.warn('[MARKET] Unable to fetch Binance data, skipping tick.');
    return;
  }

  const { closes, lastPrice } = market;
  const rsi = computeRsi(closes, CONFIG.rsiPeriod);
  const zone = classifyRsi(rsi);

  let position = await fetchPosition();
  if (!position) {
    state.activeBias = null;
  } else if (!state.activeBias) {
    state.activeBias = {
      direction: parseFloat(position.netQuantity) > 0 ? 'long' : 'short',
      anchorPrice: parseFloat(position.entryPrice),
      scaleIndex: -1,
    };
  }

  position = await maybeStopOut(position, lastPrice);
  position = await maybeTakeProfit(position, lastPrice);
  position = await maybeOpenSignal(position, zone, lastPrice);
  position = await maybeScale(position, lastPrice);

  state.lastRsiZone = zone;

  const qty = position ? parseFloat(position.netQuantity) : 0;
  const pnl = position ? computeUnrealizedPnl(position, lastPrice) : 0;
  console.log(
    `[STATUS] price=${lastPrice.toFixed(2)} rsi=${rsi.toFixed(2)} zone=${zone} qty=${qty.toFixed(4)} pnl=${pnl.toFixed(
      2,
    )}`,
  );
}

async function fetchBinanceMarket(limit = 200) {
  try {
    const url = `https://api.binance.com/api/v3/klines?symbol=${CONFIG.binanceSymbol}&interval=1m&limit=${limit}`;
    const res = await fetch(url);
    if (!res.ok) {
      throw new Error(`Binance responded with ${res.status}`);
    }
    const candles = await res.json();
    const closes = candles.map((c) => parseFloat(c[4]));
    return {
      closes,
      lastPrice: closes[closes.length - 1],
    };
  } catch (err) {
    console.error('[BINANCE ERROR]', err?.message || err);
    return null;
  }
}

function computeRsi(values, period) {
  if (values.length <= period) {
    throw new Error(`Insufficient data to compute RSI (need > ${period} values)`);
  }
  let gains = 0;
  let losses = 0;
  for (let i = 1; i <= period; i += 1) {
    const delta = values[i] - values[i - 1];
    if (delta >= 0) {
      gains += delta;
    } else {
      losses -= delta;
    }
  }
  gains /= period;
  losses /= period;

  for (let i = period + 1; i < values.length; i += 1) {
    const delta = values[i] - values[i - 1];
    if (delta >= 0) {
      gains = (gains * (period - 1) + delta) / period;
      losses = (losses * (period - 1)) / period;
    } else {
      gains = (gains * (period - 1)) / period;
      losses = (losses * (period - 1) - delta) / period;
    }
  }

  if (losses === 0) {
    return 100;
  }

  const rs = gains / losses;
  return 100 - 100 / (1 + rs);
}

function classifyRsi(value) {
  if (value >= CONFIG.rsiOverbought) {
    return 'overbought';
  }
  if (value <= CONFIG.rsiOversold) {
    return 'oversold';
  }
  return 'neutral';
}

async function fetchPosition() {
  try {
    const response = await backpackRequest({
      method: 'GET',
      path: '/api/v1/position',
      instruction: 'positionQuery',
      query: { symbol: CONFIG.symbol },
    });
    if (!Array.isArray(response) || response.length === 0) {
      return null;
    }
    const position = response.find((pos) => Math.abs(parseFloat(pos.netQuantity)) > 0);
    return position || null;
  } catch (err) {
    console.error('[POSITION ERROR]', err?.message || err);
    return null;
  }
}

async function maybeOpenSignal(position, zone, price) {
  const qty = position ? parseFloat(position.netQuantity) : 0;
  if (zone === 'overbought' && state.lastRsiZone !== 'overbought' && Math.abs(qty) < 1e-6) {
    await tryEnter('short', price);
    return fetchPosition();
  }
  if (zone === 'oversold' && state.lastRsiZone !== 'oversold' && Math.abs(qty) < 1e-6) {
    await tryEnter('long', price);
    return fetchPosition();
  }
  return position;
}

async function maybeScale(position, price) {
  if (!position || !state.activeBias) {
    return position;
  }
  const direction = state.activeBias.direction;
  const anchor = state.activeBias.anchorPrice;
  const diff = direction === 'long' ? anchor - price : price - anchor;
  if (diff <= 0) {
    state.activeBias.scaleIndex = -1;
    return position;
  }
  for (let i = state.activeBias.scaleIndex + 1; i < CONFIG.scalePlan.length; i += 1) {
    const level = CONFIG.scalePlan[i];
    if (diff >= level.threshold) {
      const remaining = remainingCapacity(position);
      if (remaining < CONFIG.minOrderSize) {
        console.log('[SCALE] Skipping scale order, position is at or above max size.');
        return position;
      }
      const orderSize = Math.min(level.quantity, remaining);
      const side = direction === 'long' ? 'Bid' : 'Ask';
      const placed = await placeMarketOrder({
        side,
        quantity: orderSize,
        reason: `Scale level ${level.threshold}`,
      });
      if (placed) {
        state.activeBias.scaleIndex = i;
        position = await fetchPosition();
      } else {
        break;
      }
    }
  }
  return position;
}

async function maybeStopOut(position, price) {
  if (!position) {
    return null;
  }
  const pnl = computeUnrealizedPnl(position, price);
  if (pnl <= -CONFIG.maxDrawdownUsd) {
    console.log('[STOP] Unrealized loss exceeded limit, closing position.');
    const closed = await flattenPosition(position, 'Stop loss > $1000');
    if (closed) {
      state.activeBias = null;
      return null;
    }
  }
  return position;
}

async function maybeTakeProfit(position, price) {
  if (!position) {
    return null;
  }
  const qty = Math.abs(parseFloat(position.netQuantity));
  if (qty < CONFIG.minOrderSize) {
    return null;
  }
  const entry = parseFloat(position.entryPrice);
  const pnl = computeUnrealizedPnl(position, price);
  const notional = entry * qty;
  const feeBudget = notional * CONFIG.takerFee * 2;
  if (pnl >= feeBudget && pnl > 0) {
    console.log('[TAKE PROFIT] Unrealized PnL covers fees, closing position.');
    const closed = await flattenPosition(position, 'Fee-covered profit');
    if (closed) {
      state.activeBias = null;
      return null;
    }
  }
  return position;
}

async function tryEnter(direction, price) {
  const side = direction === 'long' ? 'Bid' : 'Ask';
  const remaining = CONFIG.maxPositionSize;
  const qty = Math.min(CONFIG.baseOrderSize, remaining);
  if (qty < CONFIG.minOrderSize) {
    console.log('[ENTRY] Skipping entry, qty below min order size.');
    return;
  }
  const placed = await placeMarketOrder({
    side,
    quantity: qty,
    reason: `RSI ${direction === 'long' ? 'oversold' : 'overbought'} entry`,
  });
  if (placed) {
    state.activeBias = {
      direction,
      anchorPrice: price,
      scaleIndex: -1,
    };
  }
}

async function flattenPosition(position, reason) {
  if (!position) {
    return true;
  }
  const qty = parseFloat(position.netQuantity);
  if (Math.abs(qty) < CONFIG.minOrderSize) {
    return true;
  }
  const side = qty > 0 ? 'Ask' : 'Bid';
  return placeMarketOrder({
    side,
    quantity: Math.abs(qty),
    reduceOnly: true,
    reason,
  });
}

async function placeMarketOrder({ side, quantity, reduceOnly = false, reason }) {
  if (quantity < CONFIG.minOrderSize) {
    console.log('[ORDER] Skipping order, below min size.');
    return null;
  }
  const now = Date.now();
  if (now - state.lastOrderMs < CONFIG.orderCooldownMs) {
    console.log('[ORDER] Cooldown active, skipping order.');
    return null;
  }
  const payload = {
    symbol: CONFIG.symbol,
    side,
    orderType: 'Market',
    quantity: formatDecimal(quantity),
    timeInForce: 'GTC',
    reduceOnly,
  };
  try {
    const response = await backpackRequest({
      method: 'POST',
      path: '/api/v1/order',
      instruction: 'orderExecute',
      body: payload,
    });
    state.lastOrderMs = Date.now();
    console.log(`[ORDER] ${reason} -> ${response?.orderId || response?.id || 'submitted'}`);
    return response;
  } catch (err) {
    console.error('[ORDER ERROR]', err?.message || err);
    return null;
  }
}

function remainingCapacity(position) {
  const qty = position ? Math.abs(parseFloat(position.netQuantity)) : 0;
  return Math.max(0, CONFIG.maxPositionSize - qty);
}

function computeUnrealizedPnl(position, markPrice) {
  if (!position) {
    return 0;
  }
  const qty = parseFloat(position.netQuantity);
  const entry = parseFloat(position.entryPrice);
  return (markPrice - entry) * qty;
}

async function backpackRequest({ method, path, instruction, body, query }) {
  if (!instruction) {
    throw new Error('Instruction is required for signed request.');
  }
  const timestamp = Date.now().toString();
  const window = CONFIG.backpackWindow.toString();
  const params = method === 'GET' ? normalizeParams(query) : normalizeParams(body);
  const serialized = serializeParams(params);
  const segments = [`instruction=${instruction}`];
  if (serialized) {
    segments.push(serialized);
  }
  segments.push(`timestamp=${timestamp}`, `window=${window}`);
  const signingPayload = segments.join('&');
  const signature = nacl.sign.detached(Buffer.from(signingPayload), signingKey);
  const headers = {
    'Content-Type': 'application/json; charset=utf-8',
    'X-API-KEY': CONFIG.apiKey,
    'X-TIMESTAMP': timestamp,
    'X-WINDOW': window,
    'X-SIGNATURE': Buffer.from(signature).toString('base64'),
  };

  const url = new URL(path, CONFIG.backpackBaseUrl);
  if (method === 'GET' && query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, value);
      }
    });
  }

  const res = await fetch(url.toString(), {
    method,
    headers,
    body: method === 'GET' ? undefined : JSON.stringify(body),
  });

  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`Backpack ${method} ${path} failed (${res.status}): ${errorBody}`);
  }
  if (res.status === 204) {
    return null;
  }
  return res.json();
}

function normalizeParams(obj = {}) {
  const normalized = {};
  Object.entries(obj).forEach(([key, value]) => {
    if (value === undefined || value === null) {
      return;
    }
    if (typeof value === 'boolean') {
      normalized[key] = value ? 'true' : 'false';
    } else {
      normalized[key] = String(value);
    }
  });
  return normalized;
}

function serializeParams(params) {
  const keys = Object.keys(params);
  if (!keys.length) {
    return '';
  }
  return keys
    .sort()
    .map((key) => `${key}=${params[key]}`)
    .join('&');
}

function formatDecimal(value) {
  return Number(value).toFixed(6).replace(/\.?0+$/, '');
}

function parseScalePlan(raw) {
  if (!raw) {
    return DEFAULT_SCALE_PLAN;
  }
  try {
    return raw
      .split(',')
      .map((entry) => {
        const [threshold, quantity] = entry.split(':').map((n) => parseFloat(n));
        return { threshold, quantity };
      })
      .filter((item) => Number.isFinite(item.threshold) && Number.isFinite(item.quantity))
      .sort((a, b) => a.threshold - b.threshold);
  } catch {
    return DEFAULT_SCALE_PLAN;
  }
}

function guardConfig() {
  if (!process.env.BACKPACK_API_KEY || !process.env.BACKPACK_API_SECRET) {
    console.error('Missing BACKPACK_API_KEY or BACKPACK_API_SECRET.');
    process.exit(1);
  }
  const seed = Buffer.from(process.env.BACKPACK_API_SECRET, 'base64');
  if (seed.length !== 32) {
    console.error('Invalid BACKPACK_API_SECRET, expected base64-encoded 32 byte seed.');
    process.exit(1);
  }
}

main();
