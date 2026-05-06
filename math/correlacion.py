import yfinance as yf
import numpy as np
import pandas as pd

# === EJEMPLO 1: Correlación AAPL vs MSFT ===
print("=== AAPL vs MSFT ===")

# Descargar datos
data = yf.download(["AAPL", "MSFT"], period="1y", progress=False)["Close"]

# Calcular retornos diarios
retornos = data.pct_change().dropna()

# Covarianza
cov = retornos.cov()
print("\nMatriz de covarianza:")
print(cov)

# Correlación (más útil)
corr = retornos.corr()
print("\nMatriz de correlación:")
print(corr)


# === EJEMPLO 2: Tu portfolio actual del bot ===
print("\n\n=== TU PORTFOLIO (5 acciones del bot) ===")

tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
data_bot = yf.download(tickers, period="1y", progress=False)["Close"]
retornos_bot = data_bot.pct_change().dropna()

corr_bot = retornos_bot.corr()
print("\nMatriz de correlación de tus 5 acciones:")
print(corr_bot.round(3))

# Promedio de correlaciones (excluyendo diagonal)
corr_values = corr_bot.values
mask = np.triu(np.ones_like(corr_values, dtype=bool), k=1)
correlaciones_unicas = corr_values[mask]
correlacion_media = correlaciones_unicas.mean()
print(f"\nCorrelación media del portfolio: {correlacion_media:.3f}")

if correlacion_media > 0.7:
    print("→ ⚠️ Portfolio MAL diversificado (correlaciones altas)")
elif correlacion_media > 0.3:
    print("→ Portfolio diversificación moderada")
else:
    print("→ ✅ Portfolio bien diversificado")


# === EJEMPLO 3: Comparativa con activos diferentes ===
print("\n\n=== PORTFOLIO BIEN DIVERSIFICADO ===")

tickers_div = ["AAPL", "JNJ", "XOM", "TLT", "GLD"]  # Tech, Salud, Energía, Bonos, Oro
data_div = yf.download(tickers_div, period="1y", progress=False)["Close"]
retornos_div = data_div.pct_change().dropna()

corr_div = retornos_div.corr()
print("\nMatriz de correlación (multi-sector):")
print(corr_div.round(3))

mask_div = np.triu(np.ones_like(corr_div.values, dtype=bool), k=1)
corr_media_div = corr_div.values[mask_div].mean()
print(f"\nCorrelación media: {corr_media_div:.3f}")