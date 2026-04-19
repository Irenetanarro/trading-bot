# 🧠 ML Research

This directory contains the machine learning experiments that informed the Bot v2 design. Each file is a standalone research notebook exploring a specific question.

---

## Experiments Timeline

| File | Model | Main Question | Day |
|------|-------|---------------|-----|
| `ml_random_forest.py` | Random Forest | Can ML predict next-day direction? | 41 |
| `ml_xgboost.py` | XGBoost | Does XGBoost outperform Random Forest? | 42 |
| `ml_lstm.py` | LSTM (PyTorch) | Do deep learning models help? | 43 |
| `ml_walkforward.py` | Walk-forward testing | How do models hold up over time? | 44 |
| `feature_engineering.py` | 42 features | Do advanced features improve accuracy? | 45 |

---

## Key Findings

### Model Comparison (AAPL 2021-2025)

| Model | Test Accuracy | Sharpe | Return |
|-------|---------------|--------|--------|
| Random Forest | 51.37% | 0.42 | +1.47% |
| XGBoost (basic) | 52.74% | 0.45 | +12.36% |
| XGBoost (optimized) | 52.74% | 0.4471 | +42.46% |
| LSTM | 48.63% | — | — |
| Buy & Hold | — | 0.7735 | +131.90% |

**Conclusion**: XGBoost outperformed both Random Forest and LSTM. However, in strong bull markets like 2021-2025, simple Buy & Hold was superior. ML shines in bear or sideways markets — which is why Bot v2 uses ML as a confirmation filter, not a replacement for Trend Following.

### Feature Engineering Insights

Adding 22 advanced features (42 total) **decreased** performance (+44.99% → +11.70%). The top-performing new feature was `zscore_50d`, which captured mean-reversion signals missed by traditional indicators.

**Lesson learned**: More features ≠ better model. Feature selection matters more than feature quantity.

### Yearly Performance Breakdown

| Year | Buy & Hold | Trend Following | XGBoost |
|------|-----------|-----------------|---------|
| 2021 | +51% ✓ | +17% | +12% |
| 2022 | -24% | -26% | **+8% ✓** |
| 2023 | +49% ✓ | +31% | +28% |
| 2024 | +32% ✓ | +13% | +15% |

ML and Trend Following outperformed Buy & Hold **only in the bearish year 2022**. This validates using them as protective overlays in uncertain markets.

---

## Methodology Notes

- **Temporal validation**: Walk-forward testing only (no random splits, no lookahead bias)
- **Transaction costs**: Included in all backtests
- **Features**: Returns, moving averages, RSI, MACD, volatility, volume ratios
- **Target**: Binary classification (up/down next day)
