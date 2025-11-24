'use strict';

const notifier = require('node-notifier');

function sanitizeNumber(value, fallback, min = 0) {
  const parsed = Number(value);
  if (Number.isFinite(parsed) && parsed >= min) {
    return parsed;
  }
  return fallback;
}

const config = {
  backpackUrl: process.env.BACKPACK_TICKERS_URL || 'https://api.backpack.exchange/api/v1/tickers',
  lighterUrl: process.env.LIGHTER_STATS_URL || 'https://mainnet.zklighter.elliot.ai/api/v1/exchangeStats',
  backpackSymbol: process.env.BACKPACK_SYMBOL || 'BTC_USDC',
  lighterSymbol: process.env.LIGHTER_SYMBOL || 'BTC',
  pollIntervalMs: sanitizeNumber(process.env.SPREAD_POLL_INTERVAL_MS, 5000, 500),
  requestTimeoutMs: sanitizeNumber(process.env.SPREAD_REQUEST_TIMEOUT_MS, 10000, 1000),
  highThreshold: sanitizeNumber(process.env.SPREAD_ALERT_HIGH_USD, 80, 0),
  lowThreshold: sanitizeNumber(process.env.SPREAD_ALERT_LOW_USD, 10, 0),
  alertCooldownMs: sanitizeNumber(process.env.SPREAD_ALERT_COOLDOWN_MS, 60000, 0),
  notificationsEnabled: process.env.SPREAD_DISABLE_NOTIFICATIONS !== '1',
};

if (config.lowThreshold > config.highThreshold) {
  console.warn(
    '[警告] 低阈值高于高阈值，已自动对调。请检查 SPREAD_ALERT_* 环境变量的配置。',
  );
  const low = config.lowThreshold;
  config.lowThreshold = config.highThreshold;
  config.highThreshold = low;
}

const formatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const alertState = {
  high: 0,
  low: 0,
};

function formatUsd(value) {
  return formatter.format(value);
}

async function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchJson(url) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), config.requestTimeoutMs);

  try {
    const response = await fetch(url, {
      signal: controller.signal,
      headers: { accept: 'application/json' },
    });

    if (!response.ok) {
      throw new Error(`Request failed with ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error(`Request timed out after ${config.requestTimeoutMs} ms`);
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

async function getBackpackPrice() {
  const data = await fetchJson(config.backpackUrl);

  if (!Array.isArray(data)) {
    throw new Error('Unexpected response from Backpack (expected an array of tickers)');
  }

  const ticker = data.find((item) => item?.symbol === config.backpackSymbol);
  if (!ticker) {
    throw new Error(`Backpack symbol ${config.backpackSymbol} not found`);
  }

  const price = Number.parseFloat(ticker.lastPrice);
  if (!Number.isFinite(price)) {
    throw new Error(`Backpack price for ${config.backpackSymbol} is invalid: ${ticker.lastPrice}`);
  }

  return price;
}

async function getLighterPrice() {
  const data = await fetchJson(config.lighterUrl);
  const stats = Array.isArray(data?.order_book_stats) ? data.order_book_stats : [];
  const market = stats.find((item) => item?.symbol === config.lighterSymbol);

  if (!market) {
    throw new Error(`Lighter symbol ${config.lighterSymbol} not found`);
  }

  const price = Number(market.last_trade_price);
  if (!Number.isFinite(price)) {
    throw new Error(`Lighter price for ${config.lighterSymbol} is invalid: ${market.last_trade_price}`);
  }

  return price;
}

function maybeNotify(type, diff, backpackPrice, lighterPrice) {
  if (!config.notificationsEnabled) {
    return;
  }

  const now = Date.now();
  if (now - alertState[type] < config.alertCooldownMs) {
    return;
  }

  alertState[type] = now;
  const direction = backpackPrice > lighterPrice ? 'Backpack > Lighter' : 'Lighter > Backpack';
  const title =
    type === 'high'
      ? `BTC 价差超过 ${formatUsd(config.highThreshold)}`
      : `BTC 价差低于 ${formatUsd(config.lowThreshold)}`;
  const message = `${formatUsd(diff)} (${direction}) | Backpack ${formatUsd(backpackPrice)} vs Lighter ${formatUsd(
    lighterPrice,
  )}`;

  notifier.notify({
    title,
    message,
    sound: true,
    timeout: 10,
  });
}

async function pollSpread() {
  const [backpackPrice, lighterPrice] = await Promise.all([getBackpackPrice(), getLighterPrice()]);
  const diff = Math.abs(backpackPrice - lighterPrice);
  const direction = backpackPrice > lighterPrice ? 'Backpack higher' : 'Lighter higher';

  console.log(
    `[${new Date().toISOString()}] Backpack ${formatUsd(backpackPrice)} | Lighter ${formatUsd(
      lighterPrice,
    )} | Δ ${formatUsd(diff)} (${direction})`,
  );

  if (diff >= config.highThreshold) {
    maybeNotify('high', diff, backpackPrice, lighterPrice);
  } else if (diff <= config.lowThreshold) {
    maybeNotify('low', diff, backpackPrice, lighterPrice);
  }
}

async function main() {
  console.log('启动 BTC 价差监控：');
  console.log(
    `- Backpack ${config.backpackSymbol} & Lighter ${config.lighterSymbol}，每 ${config.pollIntervalMs} ms 轮询一次`,
  );
  console.log(
    `- 告警阈值：高于 ${formatUsd(config.highThreshold)} 或低于 ${formatUsd(
      config.lowThreshold,
    )}，冷却时间 ${Math.round(config.alertCooldownMs / 1000)} 秒`,
  );
  console.log(`- 桌面通知：${config.notificationsEnabled ? '已启用' : '已禁用'}`);

  while (true) {
    try {
      await pollSpread();
    } catch (error) {
      console.error(`[${new Date().toISOString()}] 监控失败：${error.message}`);
    }
    await sleep(config.pollIntervalMs);
  }
}

process.on('SIGINT', () => {
  console.log('\n已结束监控。');
  process.exit(0);
});

main().catch((error) => {
  console.error('无法启动监控：', error);
  process.exit(1);
});
