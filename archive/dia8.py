import yfinance as yf
import matplotlib.pyplot as plt

# Descargar datos de Apple
ticker = "AAPL"
data = yf.download(ticker, start="2020-01-01")

# Calcular medias móviles
data['MA20'] = data['Close'].rolling(window=20).mean()
data['MA50'] = data['Close'].rolling(window=50).mean()

# Crear el gráfico
plt.figure(figsize=(14, 7))
plt.plot(data['Close'], label='Precio de cierre', linewidth=2, alpha=0.7)
plt.plot(data['MA20'], label='Media Móvil 20 días', linewidth=2, color='orange')
plt.plot(data['MA50'], label='Media Móvil 50 días', linewidth=2, color='red')

plt.title(f'{ticker} - Precio y Medias Móviles', fontsize=16, fontweight='bold')
plt.xlabel('Fecha', fontsize=12)
plt.ylabel('Precio ($)', fontsize=12)
plt.legend(fontsize=11, loc='upper left')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# Mostrar últimos valores
print("\n--- Últimos 5 días ---")
print(data[['Close', 'MA20', 'MA50']].tail())

# Detectar señal actual
ultimo_precio = data['Close'].iloc[-1]
ultima_ma20 = data['MA20'].iloc[-1]
ultima_ma50 = data['MA50'].iloc[-1]

print(f"\n--- Señal actual ---")
print(f"Precio actual: ${ultimo_precio:.2f}")
print(f"MA20: ${ultima_ma20:.2f}")
print(f"MA50: ${ultima_ma50:.2f}")

if ultima_ma20 > ultima_ma50:
    print("🟢 SEÑAL: ALCISTA (MA20 por encima de MA50)")
else:
    print("🔴 SEÑAL: BAJISTA (MA20 por debajo de MA50)")