import yfinance as yf
import matplotlib.pyplot as plt

# Descargar datos
nvda = yf.download("NVDA", start="2020-01-01")

# Crear gráfico
plt.figure(figsize=(12, 6))
plt.plot(nvda['Close'], linewidth=2)
plt.title('Nvidia Stock Price (2020-2026)', fontsize=16)
plt.xlabel('Date', fontsize=12)
plt.ylabel('Price ($)', fontsize=12)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
