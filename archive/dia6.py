import yfinance as yf
import matplotlib.pyplot as plt

# Descargar datos de 5 empresas
tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
data = yf.download(tickers, start="2020-01-01")['Close']

# Normalizar a 100 (para comparar cambio % desde el inicio)
# Esto hace que todas empiecen en 100 y muestra el % de cambio
data_normalized = (data / data.iloc[0]) * 100

# Crear el gráfico
plt.figure(figsize=(14, 7))
for ticker in tickers:
    plt.plot(data_normalized[ticker], label=ticker, linewidth=2)

plt.title('Tech Stocks Performance Comparison (Normalized to 100)', fontsize=16, fontweight='bold')
plt.xlabel('Date', fontsize=12)
plt.ylabel('Normalized Price (Base = 100)', fontsize=12)
plt.legend(fontsize=11, loc='upper left')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# Calcular rendimiento total de cada acción
print("\n--- Rendimiento total desde 2020 ---")
for ticker in tickers:
    rendimiento = ((data[ticker].iloc[-1] / data[ticker].iloc[0]) - 1) * 100
    print(f"{ticker}: {rendimiento:+.2f}%")