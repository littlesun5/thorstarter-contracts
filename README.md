## ThorStarter Contracts

This repository contains the ThorStarter Token, Faucet and Staking contracts
used for the TGE & sale.

We're working on building out our IDO platform & governance, those contracts will
come later closer to the first project IDO. (Wouldn't wan't people to asume too
many things from reading them while they are still changing and evolving a lot)

### Building

This repository uses the `hardhat` library to test & deploy it's Solidity contracts.

`hardhat test` runs the test suite

And `hardhat run scripts/deploy.js` deploys all the scripts for the sale.

### BTC Spread Monitor

A configurable Node.js script (`scripts/monitorBtcSpread.js`) continuously compares the BTC/USDC price between:

- Backpack REST ticker feed: `https://api.backpack.exchange/api/v1/tickers` (spot symbol `BTC_USDC`)
- Lighter exchange stats: `https://mainnet.zklighter.elliot.ai/api/v1/exchangeStats` (symbol `BTC`)

Run it with:

```
npm run monitor:btc-spread
```

or `node scripts/monitorBtcSpread.js`. A desktop pop-up (powered by `node-notifier`) is triggered whenever the absolute spread exceeds \$80 or drops below \$10 by default.

You can customize behaviour through environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `SPREAD_POLL_INTERVAL_MS` | `5000` | Polling frequency in milliseconds |
| `SPREAD_REQUEST_TIMEOUT_MS` | `10000` | Per-request timeout |
| `SPREAD_ALERT_HIGH_USD` | `80` | Notify when spread ≥ this USD amount |
| `SPREAD_ALERT_LOW_USD` | `10` | Notify when spread ≤ this USD amount |
| `SPREAD_ALERT_COOLDOWN_MS` | `60000` | Minimum time between identical alerts |
| `SPREAD_DISABLE_NOTIFICATIONS` | unset | Set to `1` to disable desktop pop-ups (falls back to console logs) |
| `BACKPACK_TICKERS_URL` / `LIGHTER_STATS_URL` | defaults above | Override API endpoints |
| `BACKPACK_SYMBOL` / `LIGHTER_SYMBOL` | `BTC_USDC` / `BTC` | Override tracked symbols |

The console output always shows both prices and their spread, so you can keep the script running even without enabling system notifications.

### License

MIT
