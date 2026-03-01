import yfinance as yf
import matplotlib.pyplot as plt

# Descargar datos de 5 empresas
tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
data = yf.download(tickers, start="2020-01-01")['Close']

# Normalizar a 100 (para comparar cambio % desde inicio)
data_normalized = (data / data.iloc[0]) * 100

# Graficar
plt.figure(figsize=(12, 6))
for ticker in tickers:
    plt.plot(data_normalized[ticker], label=ticker, linewidth=2)

plt.title('Tech Stocks Performance Comparison (Normalized to 100)', fontsize=16)
plt.xlabel('Date', fontsize=12)
plt.ylabel('Normalized Price', fontsize=12)
plt.legend(fontsize=10)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()