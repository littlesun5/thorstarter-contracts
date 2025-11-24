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

## Backpack RSI Trading Bot

The `bots/backpackRsiBot.js` script automates Backpack Exchange trades using a 1‑minute RSI signal,
laddered scaling orders, fee-based take profit, and a fixed USD stop loss. Orders are signed with an
ED25519 keypair as required by Backpack's REST API.

### Configuration

1. Install dependencies (once): `npm install`
2. Copy the sample environment file and fill in your details:
   ```bash
   cp .env.example .env
   ```
3. Generate an ED25519 API key pair (per Backpack docs) and fund your account. The private seed must
   be base64 encoded and stored in `BACKPACK_SECRET`, while `BACKPACK_API_KEY` holds the base64
   public key. Leave `DRY_RUN=true` to observe signals without submitting orders.

Key environment variables:

- `BACKPACK_SYMBOL`: market symbol, defaults to `BTC_USDC_PERP`.
- `BASE_ORDER_SIZE`: base position size (0.03 BTC per spec).
- `DCA_LADDERS`: JSON array of `{threshold,size}` entries (USD distance vs. BTC size) for the
  averaging steps (defaults match the requested 150/250/500/800/1200/1500 ladder).
- `MAX_EXPOSURE_BTC`: caps total open size (defaults to 2 BTC).
- `TAKER_FEE`: used to determine when PnL covers round-trip fees (default 0.0002 = 2 bps per side).
- `MAX_LOSS_USD`: triggers the hard stop (default 1000 USD).
- `DRY_RUN`: when `true` (default) orders are only logged; set to `false` to trade live.

### Running the bot

```bash
npm run bot:rsi
```

The bot will:

- Poll Backpack klines every ~15 seconds and update a 14-period, 1-minute RSI.
- Enter a 0.03 BTC short when RSI ≥ 71 or a 0.03 BTC long when RSI ≤ 29 (only when flat).
- Respect a ≥20 second cooldown between any two orders.
- Apply the USD-denominated ladder (150/250/500/800/1200/1500) with incremental sizes
  (0.05/0.08/0.1/0.15/0.2/0.3 BTC) while keeping total exposure ≤ `MAX_EXPOSURE_BTC`.
- Close all exposure once unrealized PnL covers estimated maker/taker fees, or when drawdown reaches
  `MAX_LOSS_USD` (force-closing via a market order).

If Backpack credentials are omitted, the bot stays in observation mode: RSI signals are logged but no
positions are tracked or traded.

### License

MIT
