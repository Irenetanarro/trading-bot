import yfinance as yf

ticker = "AAPL"
data = yf.download(ticker, start="2020-01-01")

# Calcular Bandas de Bollinger
periodo = 20
num_std = 2

data['MA20'] = data['Close'].rolling(window=periodo).mean()
data['STD'] = data['Close'].rolling(window=periodo).std()

data['BB_Superior'] = data['MA20'] + (num_std * data['STD'])
data['BB_Inferior'] = data['MA20'] - (num_std * data['STD'])

print("\nBANDAS DE BOLLINGER - APPLE")
print("="*60)
print("\nULTIMOS 5 DIAS:")
print(data[['Close', 'BB_Inferior', 'MA20', 'BB_Superior']].tail())

print("\nCONTEO DE TOQUES:")
print("="*60)

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
        toques_inf = toques_inf + 1
        fechas_toque_inf.append(data.index[i])
        precios_toque_inf.append(close_val)
    
    if close_val >= bb_sup_val:
        toques_sup = toques_sup + 1
        fechas_toque_sup.append(data.index[i])
        precios_toque_sup.append(close_val)

print("Toques en banda INFERIOR:", toques_inf)
print("Toques en banda SUPERIOR:", toques_sup)
print("\nSENAL ACTUAL:")
print("="*60)

# Extraer el último valor como escalar
precio_actual = data['Close'].iloc[-1]
bb_inf = data['BB_Inferior'].iloc[-1]
bb_sup = data['BB_Superior'].iloc[-1]
ma20 = data['MA20'].iloc[-1]

# Convertir a float si es necesario
if hasattr(precio_actual, 'item'):
    precio_actual = precio_actual.item()
    bb_inf = bb_inf.item()
    bb_sup = bb_sup.item()
    ma20 = ma20.item()

print("Precio actual:", round(precio_actual, 2))
print("Banda inferior:", round(bb_inf, 2))
print("Banda media (MA20):", round(ma20, 2))
print("Banda superior:", round(bb_sup, 2))

if precio_actual <= bb_inf:
    print("\nSENAL: Precio tocando banda inferior - Posible COMPRA")
elif precio_actual >= bb_sup:
    print("\nSENAL: Precio tocando banda superior - Posible VENTA")
else:
    print("\nSENAL: Precio dentro de las bandas - NEUTRAL")

import matplotlib.pyplot as plt

print("\nGenerando grafico...")

plt.figure(figsize=(14, 8))

plt.plot(data.index, data['Close'], label='Precio', linewidth=2, color='blue')
plt.plot(data.index, data['MA20'], label='MA20 (Media)', linewidth=1.5, color='orange', linestyle='--')
plt.plot(data.index, data['BB_Superior'], label='Banda Superior', linewidth=1, color='red', linestyle='-')
plt.plot(data.index, data['BB_Inferior'], label='Banda Inferior', linewidth=1, color='green', linestyle='-')

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