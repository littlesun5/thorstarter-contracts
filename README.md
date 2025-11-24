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

### Backpack BTC RSI Bot

The repository now includes a Node.js helper (`scripts/backpackRsiBot.js`) that automates the requested BTC RSI strategy on [Backpack Exchange](https://docs.backpack.exchange/):

1. Copy `.env.example` to `.env`, then provide:
   - `BACKPACK_API_KEY`: Base64 verifying key from Backpack.
   - `BACKPACK_API_SECRET`: Base64 32-byte ED25519 seed.
   - Optional overrides such as `BASE_ORDER_SIZE`, `SCALE_PLAN`, `MAX_POSITION_SIZE`, etc.
2. Install dependencies (`npm install`) if you have not already.
3. Start the bot with `npm run bot:rsi`. The bot:
   - Pulls 1 minute BTC candles from Binance to compute RSI (default period 14).
   - Opens 0.03 BTC shorts when RSI > 71 and longs when RSI < 29.
   - Adds scaling orders following the ladder `150/250/500/800/1200/1500 USD -> 0.05/0.08/0.1/0.15/0.2/0.3 BTC`.
   - Spaces every order by at least 20 seconds, caps exposure at 2 BTC, and enforces a $1,000 stop loss.
   - Flattens positions once unrealized PnL covers expected taker fees (0.02% per side, configurable through `TAKER_FEE`).

Key environment knobs:

- `SCALE_PLAN`: Comma-separated `distance:quantity` steps (e.g. `150:0.05,250:0.08`).
- `ORDER_COOLDOWN_MS`: Milliseconds between orders (default 20000).
- `MAX_DRAWDOWN_USD`: Stop-loss threshold (default 1000).
- `MAX_POSITION_SIZE`: Hard cap on BTC exposure (default 2).

Run the bot inside a tmux/screen session for resiliency, and stop it with `Ctrl+C`. Review Backpack’s API rate limits and your account’s risk settings before going live.

### License

MIT
