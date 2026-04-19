# \# Trading Bot — ML-Powered Algorithmic Trading

# 

#[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)

# [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

# [![Commits](https://img.shields.io/badge/Commits-55%2B-brightgreen.svg)]()

#[![Status](https://img.shields.io/badge/Status-Paper%20Trading-orange.svg)]()

# 

# An algorithmic trading bot that combines classic technical analysis with machine learning to generate trading signals on US equities. Currently running on Alpaca paper trading with real-time market data.

# 

# \---

# 

## 🎯 Overview

This project is part of a 180-day self-guided bootcamp from zero programming to ML Engineer in quantitative finance. The bot implements a full pipeline: data ingestion → feature engineering → ML-based signal generation → risk management → automated order execution.

**Key principle:** ML as a confirmation filter, not a replacement for robust strategy. Trend Following signals (MA20/MA50) are validated by an XGBoost model before execution.

---

## ✨ Features

- **Dual-signal architecture**: Trend Following + XGBoost ML confirmation
- **Multi-asset monitoring**: AAPL, MSFT, GOOGL, AMZN, TSLA
- **Risk management**: Half Kelly position sizing, -10% stop loss, +20% take profit
- **Real-time execution**: Alpaca Markets API integration
- **Production logging**: CSV trade log + session history
- **Interactive dashboard**: HTML visualization of positions, P&L, and signals
- **Walk-forward validation**: Rigorous backtesting without lookahead bias

---

## 🛠️ Tech Stack

| Category | Tools |
|----------|-------|
| Language | Python 3.14 |
| Data | yfinance, pandas, NumPy |
| Machine Learning | scikit-learn, XGBoost, PyTorch |
| Broker API | Alpaca Markets |
| Visualization | Matplotlib, HTML/CSS |
| Version Control | Git, GitHub |

---

## 📂 Project Structure

tradingbot/

│

├── bot/                        # Main trading bot

│   ├── bot\_v1.py              # Trend Following only

│   ├── bot\_v2.py              # Trend Following + ML confirmation

│   ├── bot\_multi\_asset.py     # Multi-stock version

│   ├── dashboard.py           # Monitoring dashboard

│   ├── monitoring.py          # Logging system

│   └── report.py              # Report generator

│

├── research/                   # ML experiments

│   ├── ml\_random\_forest.py    # Day 41 research

│   ├── ml\_xgboost.py          # Day 42 research

│   ├── ml\_lstm.py             # Day 43 research

│   ├── ml\_walkforward.py      # Day 44 research

│   └── feature\_engineering.py # Day 45 research

│

├── analysis/                   # Exploratory analysis

├── data/                       # Datasets and outputs

├── archive/                    # Historical learning files

├── requirements.txt            # Python dependencies

└── .gitignore

\---



---

## 🚀 Installation

```bash
# Clone the repo
git clone https://github.com/Irenetanarro/tradingbot.git
cd tradingbot

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
# Create a .env file with your Alpaca paper trading API keys:
#   ALPACA_API_KEY=your_key_here
#   ALPACA_SECRET_KEY=your_secret_here
```

---

## 💻 Usage

```bash
# Run the main bot (Trend Following + ML)
python bot/bot_v2.py

# Run the multi-asset version
python bot/bot_multi_asset.py

# Generate monitoring dashboard
python bot/dashboard.py

# Generate full report
python bot/report.py
```

---

## 📊 Results

**Current Portfolio Status** (as of April 2026):

| Metric | Value |
|--------|-------|
| Initial Capital | $100,000 |
| Current Equity | $100,013.67 |
| Realized P&L | +$13.67 |
| Completed Trades | 1 |
| Win Rate | 100% (insufficient sample) |

**Note on metrics**: With only 1 completed trade, metrics like Sharpe Ratio and Win Rate are not statistically significant. A minimum of 30 trades is required for reliable evaluation. The bot is currently in cash (100%) as 4 out of 5 monitored stocks signal sell based on Death Cross confirmation.

### ML Research Results (Walk-Forward Backtesting)

| Strategy | Return | Sharpe | Max Drawdown |
|----------|--------|--------|--------------|
| XGBoost | +42.46% | 0.4471 | -30.40% |
| Trend Following | +38.02% | 0.4606 | -29.09% |
| Buy & Hold | +131.90% | 0.7735 | -33.36% |

**Key insight**: In strong bull markets (AAPL 2021-2025), Buy & Hold outperforms both strategies. ML and Trend Following provide capital protection in bear or sideways markets.

---

## 🗺️ Roadmap

- [x] Python fundamentals + financial data
- [x] Technical indicators (MA, RSI, MACD, Bollinger)
- [x] Backtesting framework with walk-forward validation
- [x] Risk management (Kelly Criterion, Stop Loss, Take Profit)
- [x] Alpaca API integration + paper trading
- [x] ML research (Random Forest, XGBoost, LSTM)
- [x] Bot v2: Trend Following + ML confirmation
- [x] Multi-asset support (5 stocks)
- [x] Professional logging and monitoring
- [ ] Probability & statistics deep dive (Day 61-70)
- [ ] Professional backtesting with vectorbt (Day 76-82)
- [ ] QuantConnect cloud backtesting (Day 83-87)
- [ ] Docker containerization (Day 91-95)
- [ ] Unit testing with pytest (Day 96-100)
- [ ] Kaggle financial competition (Day 106-113)
- [ ] Job hunting: Algo Trading Developer role

---

## ⚠️ Disclaimer

This is a paper trading project for educational purposes only. **No real money is involved.** The code is not financial advice. Past backtesting performance does not guarantee future results.

---

## 📜 License

MIT License — feel free to explore, fork, and learn.

---

## 👤 Author

**Irene Tanarro**  
Self-taught quantitative trader | Algo Trading Developer in progress

- GitHub: [@Irenetanarro](https://github.com/Irenetanarro)
- Project: [tradingbot](https://github.com/Irenetanarro/tradingbot)

*Bootcamp: Day 58 of 180 — Target: Algo Trading Developer by September 2026*
