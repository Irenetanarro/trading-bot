import yfinance as yf
import matplotlib.pyplot as plt

ticker = "AAPL"
data = yf.download(ticker, start="2020-01-01")

# Calcular medias móviles
data['MA20'] = data['Close'].rolling(window=20).mean()
data['MA50'] = data['Close'].rolling(window=50).mean()

# Calcular RSI
def calcular_rsi(data, periodo=14):
    delta = data['Close'].diff()
    ganancias = delta.where(delta > 0, 0)
    perdidas = -delta.where(delta < 0, 0)
    avg_ganancias = ganancias.rolling(window=periodo).mean()
    avg_perdidas = perdidas.rolling(window=periodo).mean()
    rs = avg_ganancias / avg_perdidas
    rsi = 100 - (100 / (1 + rs))
    return rsi

data['RSI'] = calcular_rsi(data, periodo=14)

# Detectar señales combinadas
data['Signal_MA'] = 0
data.loc[data['MA20'] > data['MA50'], 'Signal_MA'] = 1

data['Signal_RSI'] = 0
data.loc[data['RSI'] < 30, 'Signal_RSI'] = 1  # Compra en sobreventa
data.loc[data['RSI'] > 70, 'Signal_RSI'] = -1  # Venta en sobrecompra

# Señal combinada: COMPRAR solo si AMBAS señales están de acuerdo
data['Signal_Combined'] = 0
# Compra: MA alcista Y RSI en sobreventa
data.loc[(data['Signal_MA'] == 1) & (data['Signal_RSI'] == 1), 'Signal_Combined'] = 1

print("\n" + "="*60)
print("SEÑALES COMBINADAS - COMPRA SOLO SI:")
print("1. MA20 > MA50 (tendencia alcista)")
print("2. RSI < 30 (sobreventa = precio barato)")
print("="*60)

# Detectar cambios de señal
data['Position_Combined'] = data['Signal_Combined'].diff()

compras_combinadas = data[data['Position_Combined'] == 1]

print("\nSEÑALES DE COMPRA COMBINADAS - Total:", len(compras_combinadas))
print("-" * 60)

for idx in compras_combinadas.index:
    fecha = str(idx)[:10]
    precio_value = data.loc[idx, 'Close']
    precio = float(precio_value.iloc[0]) if hasattr(precio_value, 'iloc') else float(precio_value)
    rsi_value = data.loc[idx, 'RSI']
    rsi = float(rsi_value.iloc[0]) if hasattr(rsi_value, 'iloc') else float(rsi_value)
    print("Fecha:", fecha, "| Precio: $", round(precio, 2), "| RSI:", round(rsi, 2))

print("\n" + "="*60)
print("COMPARACION:")
print("Señales solo con MA:", "18 golden crosses")
print("Señales combinadas (MA + RSI):", len(compras_combinadas))
print("="*60)
print("\nReduccion de señales falsas:", round((1 - len(compras_combinadas)/18) * 100, 1), "%")

# Análisis correcto
total_sobreventa = len(data[data['RSI'] < 30])
total_combinadas = len(compras_combinadas)

print("\n" + "="*60)
print("ANALISIS CORRECTO:")
print("="*60)
print("Veces que RSI < 30 (sobreventa):", total_sobreventa)
print("De esas, cuantas con tendencia alcista (MA20 > MA50):", total_combinadas)
print("Señales falsas eliminadas:", total_sobreventa - total_combinadas)
print("Porcentaje de filtrado:", round((1 - total_combinadas/total_sobreventa) * 100, 1), "%")
print("="*60)