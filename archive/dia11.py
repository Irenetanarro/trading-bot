import yfinance as yf
import matplotlib.pyplot as plt

ticker = "AAPL"
data = yf.download(ticker, start="2020-01-01")

# Calcular Bandas de Bollinger
periodo = 20
num_std = 2

data['MA20'] = data['Close'].rolling(window=periodo).mean()
data['STD'] = data['Close'].rolling(window=periodo).std()

data['BB_Superior'] = data['MA20'] + (num_std * data['STD'])
data['BB_Inferior'] = data['MA20'] - (num_std * data['STD'])

print("\n" + "="*60)
print("BANDAS DE BOLLINGER - APPLE")
print("="*60)

# Contar toques manualmente
toques_inf = 0
toques_sup = 0

fechas_toque_inf = []
precios_toque_inf = []
fechas_toque_sup = []
precios_toque_sup = []

for i in range(len(data)):
    close_val = data['Close'].values[i]
    bb_inf_val = data['BB_Inferior'].values[i]
    bb_sup_val = data['BB_Superior'].values[i]
    
    if close_val <= bb_inf_val:
        toques_inf += 1
        fechas_toque_inf.append(data.index[i])
        precios_toque_inf.append(close_val)
    
    if close_val >= bb_sup_val:
        toques_sup += 1
        fechas_toque_sup.append(data.index[i])
        precios_toque_sup.append(close_val)

print("\nToques en banda INFERIOR (compra):", toques_inf)
print("Toques en banda SUPERIOR (venta):", toques_sup)

# Mostrar últimos valores
print("\n" + "="*60)
print("ULTIMOS 5 DIAS:")
print("="*60)
print(data[['Close', 'BB_Inferior', 'MA20', 'BB_Superior']].tail())

# Señal actual
precio_actual = float(data['Close'].values[-1])
bb_inf = float(data['BB_Inferior'].values[-1])
bb_sup = float(data['BB_Superior'].values[-1])
ma20 = float(data['MA20'].values[-1])

print("\n" + "="*60)
print("SEÑAL ACTUAL:")
print("="*60)
print("Precio actual: $", round(precio_actual, 2))
print("Banda inferior: $", round(bb_inf, 2))
print("Banda media (MA20): $", round(ma20, 2))
print("Banda superior: $", round(bb_sup, 2))

distancia_inf = ((precio_actual - bb_inf) / bb_inf) * 100
distancia_sup = ((bb_sup - precio_actual) / precio_actual) * 100

print("\nDistancia a banda inferior:", round(distancia_inf, 2), "%")
print("Distancia a banda superior:", round(distancia_sup, 2), "%")

if precio_actual <= bb_inf:
    print("\nSEÑAL: Precio tocando banda inferior - Posible COMPRA")
elif precio_actual >= bb_sup:
    print("\nSEÑAL: Precio tocando banda superior - Posible VENTA")
else:
    print("\nSEÑAL: Precio dentro de las bandas - NEUTRAL")

# Crear gráfico
plt.figure(figsize=(14, 8))

plt.plot(data.index, data['Close'], label='Precio', linewidth=2, color='blue')
plt.plot(data.index, data['MA20'], label='MA20 (Media)', linewidth=1.5, color='orange', linestyle='--')
plt.plot(data.index, data['BB_Superior'], label='Banda Superior', linewidth=1, color='red', linestyle='-')
plt.plot(data.index, data['BB_Inferior'], label='Banda Inferior', linewidth=1, color='green', linestyle='-')

# Rellenar área entre bandas
plt.fill_between(data.index, data['BB_Inferior'], data['BB_Superior'], alpha=0.1, color='gray')

# Marcar toques
if len(fechas_toque_inf) > 0:
    plt.scatter(fechas_toque_inf, precios_toque_inf, color='green', s=50, marker='^', 
                label='Toque banda inferior', zorder=5)

if len(fechas_toque_sup) > 0:
    plt.scatter(fechas_toque_sup, precios_toque_sup, color='red', s=50, marker='v', 
                label='Toque banda superior', zorder=5)

plt.title('AAPL - Bandas de Bollinger', fontsize=16, fontweight='bold')
plt.xlabel('Fecha', fontsize=12)
plt.ylabel('Precio ($)', fontsize=12)
plt.legend(fontsize=10, loc='upper left')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()