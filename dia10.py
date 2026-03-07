import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd

# Descargar datos de Apple
ticker = "AAPL"
data = yf.download(ticker, start="2020-01-01")

# Calcular RSI
def calcular_rsi(data, periodo=14):
    # Calcular cambios de precio
    delta = data['Close'].diff()
    
    # Separar ganancias y pérdidas
    ganancias = delta.where(delta > 0, 0)
    perdidas = -delta.where(delta < 0, 0)
    
    # Calcular promedio de ganancias y pérdidas
    avg_ganancias = ganancias.rolling(window=periodo).mean()
    avg_perdidas = perdidas.rolling(window=periodo).mean()
    
    # Calcular RS (Relative Strength)
    rs = avg_ganancias / avg_perdidas
    
    # Calcular RSI
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

# Calcular RSI de 14 días
data['RSI'] = calcular_rsi(data, periodo=14)

# Mostrar últimos valores
print("\n" + "="*60)
print("RSI DE APPLE - ULTIMOS 10 DIAS")
print("="*60)
print(data[['Close', 'RSI']].tail(10))

# Detectar señales actuales
ultimo_rsi = data['RSI'].iloc[-1]
print("\n" + "="*60)
print("SEÑAL ACTUAL")
print("="*60)
print("RSI actual:", round(ultimo_rsi, 2))

if ultimo_rsi > 70:
    print("🔴 SOBRECOMPRA - Posible corrección a la baja")
elif ultimo_rsi < 30:
    print("🟢 SOBREVENTA - Posible rebote al alza")
else:
    print("⚪ NEUTRAL - Sin señal clara")

# Crear gráfico con precio y RSI
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

# Gráfico 1: Precio
ax1.plot(data.index, data['Close'], linewidth=2, color='blue')
ax1.set_ylabel('Precio ($)', fontsize=12)
ax1.set_title(ticker + ' - Precio y RSI', fontsize=16, fontweight='bold')
ax1.grid(True, alpha=0.3)

# Gráfico 2: RSI
ax2.plot(data.index, data['RSI'], linewidth=2, color='purple')
ax2.axhline(y=70, color='red', linestyle='--', linewidth=1, label='Sobrecompra (70)')
ax2.axhline(y=30, color='green', linestyle='--', linewidth=1, label='Sobreventa (30)')
ax2.axhline(y=50, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
ax2.fill_between(data.index, 70, 100, alpha=0.2, color='red')
ax2.fill_between(data.index, 0, 30, alpha=0.2, color='green')
ax2.set_ylabel('RSI', fontsize=12)
ax2.set_xlabel('Fecha', fontsize=12)
ax2.set_ylim(0, 100)
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()