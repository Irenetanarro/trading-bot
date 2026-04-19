# 🤖 Trading Bot

This directory contains the core trading bot implementation with Alpaca paper trading integration.

---

## Evolution

| Version | File | Description |
|---------|------|-------------|
| v1 | `bot_v1.py` | Trend Following only (MA20/MA50 crossover) |
| v2 | `bot_v2_initial.py` | First version integrating XGBoost ML confirmation |
| v2 | `bot_v2.py` | Production version with risk management |
| multi | `bot_multi_asset.py` | Multi-asset monitoring (5 stocks) |

---

## Supporting Modules

| File | Purpose |
|------|---------|
| `alpaca_setup.py` | Initial Alpaca API connection and account verification |
| `first_order.py` | First test order to validate API integration |
| `dashboard.py` | Real-time monitoring dashboard (HTML + console) |
| `monitoring.py` | Professional logging system (CSV trade log + session history) |
| `report.py` | Generates full performance report |

---
1. Data Ingestion → yfinance (historical) + Alpaca (real-time)
2. Signal Generation → MA20/MA50 Crossover (primary)
3. ML Confirmation → XGBoost filter (veto on RSI overbought)
4. Risk Management → Half Kelly sizing + Stop Loss (-10%) + Take Profit (+20%)
5. Order Execution → Alpaca Markets API
6. Logging → CSV + session logs

---

## Current Behavior

The bot operates conservatively by design:

- **Enters** on Golden Cross (MA20 > MA50) confirmed by XGBoost
- **Exits** on Death Cross (MA20 < MA50) or risk thresholds triggered
- **Holds cash** when signals are unclear or bearish (current state)

This low-frequency approach is intentional — Trend Following strategies typically execute 10-30 trades per year per asset, prioritizing capital preservation over constant activity.

---

## Quick Start

```bash
# From the repo root
python bot/bot_v2.py              # Run main bot
python bot/bot_multi_asset.py     # Run multi-asset version
python bot/dashboard.py           # View current status
```

Requires a `.env` file in the repo root with Alpaca paper trading credentials.
## Architecture (Bot v2)
