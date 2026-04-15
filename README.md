# Binance Futures Testnet Trading Bot

Small Python CLI app for placing `MARKET` and `LIMIT` orders on Binance USDT-M Futures Testnet using direct signed REST calls.

## Features
- Places `MARKET` and `LIMIT` orders on Binance Futures Testnet
- Supports both `BUY` and `SELL`
- Separates CLI, validation, and API client logic
- Logs requests, responses, and errors to a file without exposing secrets
- Handles validation errors, API errors, and network failures cleanly

## Project Structure
```text
.
├── bot/
│   ├── __init__.py
│   ├── client.py
│   ├── exceptions.py
│   ├── logging_config.py
│   ├── orders.py
│   └── validators.py
├── cli.py
├── logs/
├── requirements.txt
└── tests/
```

## Setup
1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Export Binance Futures Testnet credentials:

```bash
export BINANCE_API_KEY="your_testnet_api_key"
export BINANCE_API_SECRET="your_testnet_api_secret"
```

Or create a local `.env` file in the project root:

```bash
cat > .env <<'EOF'
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret
BINANCE_BASE_URL=https://testnet.binancefuture.com
EOF
```

Optional:

```bash
export BINANCE_BASE_URL="https://testnet.binancefuture.com"
```

## How to Run
Market order example:

```bash
python3 cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001 --log-file logs/market_order.log
```

Limit order example:

```bash
python3 cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 70000 --log-file logs/limit_order.log
```

If your credentials are stored somewhere else, pass the file explicitly:

```bash
python3 cli.py --env-file /path/to/.env --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

Example output:

```text
Order Request Summary
  Symbol: BTCUSDT
  Side: BUY
  Type: MARKET
  Quantity: 0.001
Order Response Details
  Order ID: 123456789
  Status: FILLED
  Executed Quantity: 0.001
  Average Price: 68000.50
Success: order submitted to Binance Futures Testnet.
```

## Running Tests
```bash
python3 -m unittest discover -s tests -v
```

## Assumptions
- The bot targets Binance USDT-M Futures Testnet only.
- `LIMIT` orders use `GTC` by default.
- One-way mode is assumed. Hedge-mode `positionSide` handling is intentionally out of scope.
- `avgPrice` can be unavailable or zero for an unfilled limit order, so the CLI prints `N/A` only when Binance omits the field entirely.

## Notes on Logs
- The CLI writes logs to `logs/trading_bot.log` by default.
- You can override the destination with `--log-file`.
- The CLI also reads credentials from `.env` by default, or from a custom path via `--env-file`.
- Secrets and signatures are never written to the logs.

## Deliverable Notes
- The repository includes the code, tests, and log directory structure required for submission.
- Live `MARKET` and `LIMIT` log files can be generated with the commands above once valid Binance Futures Testnet credentials are exported in the shell.
