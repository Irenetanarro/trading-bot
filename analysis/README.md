# 📊 Exploratory Analysis

This directory contains exploratory analysis scripts focused on understanding market data, validating indicators, and measuring bot performance.

---

## Scripts

| File | Purpose | Day |
|------|---------|-----|
| `3Indicator_AAPL.py` | Combined analysis of RSI, MACD, and volatility on AAPL | 55 |
| `MA_Review.py` | Moving averages deep dive with live market data | 54 |
| `metricas_bot.py` | Performance metrics calculation (Sharpe, Drawdown, Win Rate) from live Alpaca data | 56 |
| `verificacion.py` | System verification script |

---

## Key Insights

### Technical Indicators (Day 55 Analysis)

Current AAPL state demonstrated how indicators operating on different time windows can tell different stories without being contradictory:

- **RSI (14-day)**: 73.4 → Overbought
- **MACD (short-term)**: Above Signal → Bullish momentum
- **MA20/MA50 (medium-term)**: Death Cross → Bearish trend

A good trader combines multiple indicators to confirm signals rather than debating which one is "right".

### Bot Performance Assessment (Day 56)

With only 1 completed trade, the bot's current metrics (100% Win Rate, 0% Drawdown) are not statistically significant. This is an honest acknowledgment — 30+ trades and 6-12 months of operation are needed for reliable evaluation.

What **can** be defended:
- The system executed its design correctly (entry on Golden Cross, exit on Death Cross)
- Cash position is valid when monitored assets show bearish signals
- The bot is free from the action bias that plagues retail traders
