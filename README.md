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

Run `npm run monitor:btc` to start a lightweight watcher that compares Backpack (`BTC_USDC`) 与 Lighter (`market_id=1`) 的 BTC 现货价格差。  
默认每 5 秒拉取一次，当价差大于 `80 USD` 或小于 `10 USD` 时会通过桌面通知弹窗提醒。  
可以通过环境变量定制行为：

```
POLL_INTERVAL_MS=3000 ALERT_UPPER_USD=100 ALERT_LOWER_USD=5 npm run monitor:btc
```

更多可选变量：

- `BACKPACK_ENDPOINT`, `BACKPACK_SYMBOL`
- `LIGHTER_ENDPOINT`, `LIGHTER_MARKET_ID`, `LIGHTER_LIMIT`
- `ALERT_COOLDOWN_MS`, `FETCH_TIMEOUT_MS`

### License

MIT
