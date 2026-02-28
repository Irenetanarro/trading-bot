import yfinance as yf

# Descargar datos de Apple
aapl = yf.download("AAPL", start="2020-01-01")
aapl['Returns'] = aapl['Close'].pct_change()

# Calcular volatilidad (desviación estándar de retornos)
volatilidad_diaria = aapl['Returns'].std()
volatilidad_anualizada = volatilidad_diaria * (252 ** 0.5)  # 252 = días de trading al año

print(f"Volatilidad diaria: {volatilidad_diaria:.4f}")
print(f"Volatilidad anualizada: {volatilidad_anualizada:.2%}")

# EXTRA: Comparar volatilidad de varias empresas
print("\n--- Comparación de volatilidad ---")
tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

for ticker in tickers:
    data = yf.download(ticker, start="2020-01-01", progress=False)
    data['Returns'] = data['Close'].pct_change()
    vol = data['Returns'].std() * (252 ** 0.5)
    print(f"{ticker}: {vol:.2%}")