import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

ticker = "AAPL"
data = yf.download(ticker, start="2020-01-01", group_by='ticker')

# Si viene con multi-index, aplanarlo
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.droplevel(0)

print("\n" + "="*70)
print("MAXIMUM DRAWDOWN - APPLE (2020-2026)")
print("="*70)

# Función para calcular drawdown
def calcular_drawdown(precios):
    if isinstance(precios, pd.DataFrame):
        precios = precios.iloc[:, 0]
    
    max_acumulado = precios.cummax()
    drawdown = (precios - max_acumulado) / max_acumulado
    max_drawdown = drawdown.min()
    
    return drawdown, max_drawdown

# BUY AND HOLD
print("\n[1] BUY AND HOLD")
print("-" * 70)

precios_close = data['Close']
if isinstance(precios_close, pd.DataFrame):
    precios_close = precios_close.iloc[:, 0]

capital_bh = 10000 * (precios_close / precios_close.iloc[0])
drawdown_bh, mdd_bh = calcular_drawdown(capital_bh)

if hasattr(mdd_bh, 'item'):
    mdd_bh = mdd_bh.item()

print("Maximum Drawdown:", round(mdd_bh * 100, 2), "%")

fecha_peor = drawdown_bh.idxmin()
print("Fecha del peor drawdown:", str(fecha_peor)[:10])

pico_antes = capital_bh.loc[:fecha_peor].max()
valle = capital_bh.loc[fecha_peor]

if hasattr(pico_antes, 'item'):
    pico_antes = pico_antes.item()
if hasattr(valle, 'item'):
    valle = valle.item()

print("Pico antes de la caida: $", int(pico_antes))
print("Valle mas bajo: $", int(valle))
print("Perdida desde el pico: $", int(valle - pico_antes))

# MEDIAS MOVILES
print("\n[2] MEDIAS MOVILES")
print("-" * 70)

data['MA20'] = data['Close'].rolling(window=20).mean()
data['MA50'] = data['Close'].rolling(window=50).mean()
data['Signal_MA'] = 0
data.loc[data['MA20'] > data['MA50'], 'Signal_MA'] = 1
data['Position_MA'] = data['Signal_MA'].diff()

# Simular capital
capital_ma = 10000.0
shares = 0.0
capital_history = []

for i in range(len(data)):
    pos = data['Position_MA'].values[i]
    precio = data['Close'].values[i]
    
    if pos == 1.0 and shares == 0.0:
        shares = capital_ma / precio
    elif pos == -1.0 and shares > 0.0:
        capital_ma = shares * precio
        shares = 0.0
    
    if shares > 0.0:
        capital_history.append(shares * precio)
    else:
        capital_history.append(capital_ma)

capital_ma_series = pd.Series(capital_history, index=data.index)
drawdown_ma, mdd_ma = calcular_drawdown(capital_ma_series)

if hasattr(mdd_ma, 'item'):
    mdd_ma = mdd_ma.item()

print("Maximum Drawdown:", round(mdd_ma * 100, 2), "%")

fecha_peor_ma = drawdown_ma.idxmin()
print("Fecha del peor drawdown:", str(fecha_peor_ma)[:10])

pico_antes_ma = capital_ma_series.loc[:fecha_peor_ma].max()
valle_ma = capital_ma_series.loc[fecha_peor_ma]

if hasattr(pico_antes_ma, 'item'):
    pico_antes_ma = pico_antes_ma.item()
if hasattr(valle_ma, 'item'):
    valle_ma = valle_ma.item()

print("Pico antes de la caida: $", int(pico_antes_ma))
print("Valle mas bajo: $", int(valle_ma))
print("Perdida desde el pico: $", int(valle_ma - pico_antes_ma))

# RANKING
print("\n" + "="*70)
print("RANKING POR MAXIMUM DRAWDOWN (menor es mejor)")
print("="*70)

estrategias_mdd = [
    ("Buy and Hold", mdd_bh * 100),
    ("Medias Moviles", mdd_ma * 100)
]

estrategias_mdd_ordenadas = sorted(estrategias_mdd, key=lambda x: x[1])

for i in range(len(estrategias_mdd_ordenadas)):
    nombre = estrategias_mdd_ordenadas[i][0]
    mdd = estrategias_mdd_ordenadas[i][1]
    
    if mdd > -10:
        calificacion = "EXCELENTE"
    elif mdd > -20:
        calificacion = "BUENO"
    elif mdd > -30:
        calificacion = "ACEPTABLE"
    else:
        calificacion = "ALTO RIESGO"
    
    print(str(i+1) + ". " + nombre + " - MDD: " + str(round(mdd, 2)) + "% - " + calificacion)

print("\nREFERENCIA:")
print("Estrategias profesionales buenas: MDD < -20%")
print("Estrategias profesionales excelentes: MDD < -10%")
print("S&P 500 en crisis 2008: MDD = -55%")
print("="*70)

# GRAFICO
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

ax1.plot(data.index, capital_bh, label='Buy and Hold', linewidth=2, color='blue')
ax1.plot(capital_ma_series.index, capital_ma_series, label='Medias Moviles', linewidth=2, color='orange')
ax1.set_ylabel('Capital ($)', fontsize=12)
ax1.set_title('Capital y Drawdown - Apple 2020-2026', fontsize=16, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)

ax2.fill_between(data.index, drawdown_bh * 100, 0, alpha=0.3, color='blue', label='Buy and Hold')
ax2.fill_between(drawdown_ma.index, drawdown_ma * 100, 0, alpha=0.3, color='orange', label='Medias Moviles')
ax2.set_ylabel('Drawdown (%)', fontsize=12)
ax2.set_xlabel('Fecha', fontsize=12)
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)
ax2.axhline(y=-20, color='red', linestyle='--', linewidth=1)

plt.tight_layout()
plt.show()