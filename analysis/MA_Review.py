import yfinance as yf

# Descargar datos
data = yf.download("AAPL", period="3mo", progress=False)
if data.columns.nlevels > 1:
    data.columns = data.columns.get_level_values(0)

# Calcular medias móviles
data["MA20"] = data["Close"].rolling(20).mean()
data["MA50"] = data["Close"].rolling(50).mean()

# Últimos valores
precio_hoy = float(data["Close"].iloc[-1])
ma20_hoy = float(data["MA20"].iloc[-1])
ma50_hoy = float(data["MA50"].iloc[-1])

# Mostrar estado actual
print(f"Precio actual: ${precio_hoy:.2f}")
print(f"MA20: ${ma20_hoy:.2f}")
print(f"MA50: ${ma50_hoy:.2f}")

# Detectar señal
if ma20_hoy > ma50_hoy:
    print("🟢 GOLDEN CROSS → Tendencia alcista → COMPRAR")
else:
    print("🔴 DEATH CROSS → Tendencia bajista → VENDER")