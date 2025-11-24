#!/usr/bin/env node
'use strict';

const notifier = require('node-notifier');

const BACKPACK_ENDPOINT =
  process.env.BACKPACK_ENDPOINT ||
  'https://api.backpack.exchange/api/v1/tickers?products=BTC_USDC';
const BACKPACK_SYMBOL = process.env.BACKPACK_SYMBOL || 'BTC_USDC';

const LIGHTER_ENDPOINT =
  process.env.LIGHTER_ENDPOINT ||
  'https://mainnet.zklighter.elliot.ai/api/v1/recentTrades';
const LIGHTER_MARKET_ID = Number(process.env.LIGHTER_MARKET_ID || '1');
const LIGHTER_LIMIT = Number(process.env.LIGHTER_LIMIT || '1');

const POLL_INTERVAL_MS = Number(process.env.POLL_INTERVAL_MS || '5000');
const ALERT_UPPER_USD = Number(process.env.ALERT_UPPER_USD || '80');
const ALERT_LOWER_USD = Number(process.env.ALERT_LOWER_USD || '10');
const ALERT_COOLDOWN_MS = Number(process.env.ALERT_COOLDOWN_MS || '60000');
const FETCH_TIMEOUT_MS = Number(process.env.FETCH_TIMEOUT_MS || '10000');

let lastAlertState = 'normal';
let lastAlertAt = 0;
let shuttingDown = false;

function formatTs(ts = Date.now()) {
  return new Date(ts).toLocaleString('zh-CN', {
    hour12: false,
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

function log(message) {
  console.log(`[${formatTs()}] ${message}`);
}

async function fetchJson(url, sourceName) {
  const controller = AbortSignal.timeout(FETCH_TIMEOUT_MS);
  const res = await fetch(url, {
    headers: { accept: 'application/json' },
    signal: controller
  });

  if (!res.ok) {
    throw new Error(`${sourceName} HTTP ${res.status}`);
  }

  return res.json();
}

async function fetchBackpackPrice() {
  const data = await fetchJson(BACKPACK_ENDPOINT, 'Backpack');
  if (!Array.isArray(data)) {
    throw new Error('Backpack 响应不是数组');
  }

  const ticker = data.find((item) => item.symbol === BACKPACK_SYMBOL);
  if (!ticker || ticker.lastPrice === undefined) {
    throw new Error(`未找到 Backpack 交易对 ${BACKPACK_SYMBOL}`);
  }

  const price = Number(ticker.lastPrice);
  if (Number.isNaN(price)) {
    throw new Error('Backpack 价格无法解析');
  }

  return price;
}

async function fetchLighterPrice() {
  const url = new URL(LIGHTER_ENDPOINT);
  if (!url.searchParams.has('market_id')) {
    url.searchParams.set('market_id', String(LIGHTER_MARKET_ID));
  }
  if (!url.searchParams.has('limit')) {
    url.searchParams.set('limit', String(LIGHTER_LIMIT));
  }

  const data = await fetchJson(url, 'Lighter');
  const trade = data?.trades?.[0];
  if (!trade || trade.price === undefined) {
    throw new Error('Lighter 未返回成交数据');
  }

  const price = Number(trade.price);
  if (Number.isNaN(price)) {
    throw new Error('Lighter 价格无法解析');
  }

  return price;
}

function maybeNotify(state, diff, backpackPrice, lighterPrice) {
  if (state === 'normal') {
    if (lastAlertState !== 'normal') {
      log('价差已回到正常区间');
      lastAlertState = 'normal';
    }
    return;
  }

  const now = Date.now();
  if (state === lastAlertState && now - lastAlertAt < ALERT_COOLDOWN_MS) {
    return;
  }

  lastAlertState = state;
  lastAlertAt = now;

  const diffStr = diff.toFixed(2);
  const backpackStr = backpackPrice.toFixed(2);
  const lighterStr = lighterPrice.toFixed(2);

  const title =
    state === 'high'
      ? 'BTC 跨所价差 > 上限'
      : 'BTC 跨所价差 < 下限';
  const message = `差价: ${diffStr} USD\nBackpack: ${backpackStr}\nLighter: ${lighterStr}`;

  notifier.notify(
    {
      title,
      message,
      sound: true,
      wait: false,
      timeout: 5
    },
    (err) => {
      if (err) {
        console.error('发送桌面通知失败：', err.message);
      }
    }
  );

  log(`触发提醒 (${title}): ${message.replace(/\n/g, ' | ')}`);
}

async function pollOnce() {
  const [backpackPrice, lighterPrice] = await Promise.all([
    fetchBackpackPrice(),
    fetchLighterPrice()
  ]);

  const diff = Math.abs(backpackPrice - lighterPrice);
  const state =
    diff > ALERT_UPPER_USD
      ? 'high'
      : diff < ALERT_LOWER_USD
        ? 'low'
        : 'normal';

  log(
    `Backpack: ${backpackPrice.toFixed(2)} | Lighter: ${lighterPrice.toFixed(
      2
    )} | 差价: ${diff.toFixed(2)} USD`
  );
  maybeNotify(state, diff, backpackPrice, lighterPrice);
}

async function main() {
  log(
    `启动监控 (周期 ${POLL_INTERVAL_MS}ms, 上限 ${ALERT_UPPER_USD} USD, 下限 ${ALERT_LOWER_USD} USD)`
  );
  while (!shuttingDown) {
    const started = Date.now();
    try {
      await pollOnce();
    } catch (err) {
      console.error(`[${formatTs()}] 拉取失败: ${err.message}`);
    }
    const elapsed = Date.now() - started;
    const waitMs = Math.max(POLL_INTERVAL_MS - elapsed, 0);
    await new Promise((resolve) => setTimeout(resolve, waitMs));
  }
}

process.on('SIGINT', () => {
  shuttingDown = true;
  log('收到退出信号，准备停止...');
  setTimeout(() => process.exit(0), 200);
});

main().catch((err) => {
  console.error('监控进程异常退出：', err);
  process.exit(1);
});
