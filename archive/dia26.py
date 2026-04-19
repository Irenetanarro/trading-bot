import yfinance as yf
import pandas as pd
import numpy as np

ticker = "AAPL"
data = yf.download(ticker, start="2020-01-01", end="2026-03-24", group_by='ticker')

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.droplevel(0)

print("\n" + "="*80)
print("MEAN REVERSION STRATEGY - APPLE")
print("="*80)

# Calcular media móvil y desviación estándar
window = 20
data['MA20'] = data['Close'].rolling(window=window).mean()
data['STD20'] = data['Close'].rolling(window=window).std()

# Bandas de Bollinger (media +/- 2 desviaciones estándar)
data['Upper_Band'] = data['MA20'] + (2 * data['STD20'])
data['Lower_Band'] = data['MA20'] - (2 * data['STD20'])

# Z-score (cuántas desviaciones estándar está el precio de la media)
data['Z_Score'] = (data['Close'] - data['MA20']) / data['STD20']

print("\nIndicadores actuales:")
print(f"Precio actual: ${data['Close'].iloc[-1]:.2f}")
print(f"Media 20 días: ${data['MA20'].iloc[-1]:.2f}")
print(f"Banda superior: ${data['Upper_Band'].iloc[-1]:.2f}")
print(f"Banda inferior: ${data['Lower_Band'].iloc[-1]:.2f}")
print(f"Z-Score actual: {data['Z_Score'].iloc[-1]:.2f}")

if data['Z_Score'].iloc[-1] > 2:
    print("\nSEÑAL: SOBRECOMPRADO - Considerar VENDER")
elif data['Z_Score'].iloc[-1] < -2:
    print("\nSEÑAL: SOBREVENDIDO - Considerar COMPRAR")
else:
    print("\nSEÑAL: NEUTRAL - No operar")

# BACKTESTING
print("\n" + "="*80)
print("BACKTESTING - MEAN REVERSION vs BUY AND HOLD")
print("="*80)

# Estrategia Mean Reversion
capital = 10000.0
shares = 0.0
operaciones = []

for i in range(window, len(data)):
    precio = data['Close'].iloc[i]
    z_score = data['Z_Score'].iloc[i]
    
    # COMPRAR cuando está sobrevendido (Z < -2)
    if z_score < -2 and shares == 0:
        shares = capital / precio
        precio_compra = precio
        fecha_compra = data.index[i]
    
    # VENDER cuando vuelve a la media o está sobrecomprado (Z > 0)
    elif z_score > 0 and shares > 0:
        capital = shares * precio
        ganancia = capital - 10000
        
        operaciones.append({
            'fecha_compra': fecha_compra,
            'precio_compra': precio_compra,
            'fecha_venta': data.index[i],
            'precio_venta': precio,
            'ganancia': ganancia,
            'retorno': (precio / precio_compra - 1) * 100
        })
        
        shares = 0
        capital = 10000

# Venta final
if shares > 0:
    precio_final = data['Close'].iloc[-1]
    capital = shares * precio_final
    ganancia = capital - 10000
    
    operaciones.append({
        'fecha_compra': fecha_compra,
        'precio_compra': precio_compra,
        'fecha_venta': data.index[-1],
        'precio_venta': precio_final,
        'ganancia': ganancia,
        'retorno': (precio_final / precio_compra - 1) * 100
    })

capital_mean_reversion = capital if shares == 0 else shares * data['Close'].iloc[-1]
retorno_mr = ((capital_mean_reversion / 10000) - 1) * 100

# Buy and Hold
precio_inicial = data['Close'].iloc[window]
precio_final = data['Close'].iloc[-1]
capital_bh = 10000 * (precio_final / precio_inicial)
retorno_bh = ((capital_bh / 10000) - 1) * 100

# Resultados
print(f"\nMEAN REVERSION:")
print(f"  Capital final: ${int(capital_mean_reversion):,}")
print(f"  Retorno: {retorno_mr:+.2f}%")
print(f"  Operaciones: {len(operaciones)}")

if operaciones:
    ganancias = [op['ganancia'] for op in operaciones if op['ganancia'] > 0]
    perdidas = [op['ganancia'] for op in operaciones if op['ganancia'] <= 0]
    
    win_rate = len(ganancias) / len(operaciones) * 100 if operaciones else 0
    print(f"  Win rate: {win_rate:.1f}%")
    
    if ganancias and perdidas:
        avg_win = np.mean(ganancias)
        avg_loss = abs(np.mean(perdidas))
        print(f"  Ganancia promedio: ${avg_win:,.0f}")
        print(f"  Pérdida promedio: ${avg_loss:,.0f}")

print(f"\nBUY AND HOLD:")
print(f"  Capital final: ${int(capital_bh):,}")
print(f"  Retorno: {retorno_bh:+.2f}%")

ventaja = retorno_mr - retorno_bh
print(f"\nVENTAJA MEAN REVERSION: {ventaja:+.2f}%")

if ventaja > 0:
    print("Mean Reversion GANÓ a Buy and Hold")
else:
    print("Buy and Hold GANÓ a Mean Reversion")

# Mostrar algunas operaciones
if operaciones:
    print("\n" + "="*80)
    print("PRIMERAS 5 OPERACIONES")
    print("="*80)
    
    for i, op in enumerate(operaciones[:5], 1):
        print(f"\nOperación {i}:")
        print(f"  Compra: {op['fecha_compra'].strftime('%Y-%m-%d')} a ${op['precio_compra']:.2f}")
        print(f"  Venta: {op['fecha_venta'].strftime('%Y-%m-%d')} a ${op['precio_venta']:.2f}")
        print(f"  Retorno: {op['retorno']:+.2f}%")
        print(f"  Ganancia: ${op['ganancia']:+,.0f}")

print("\n" + "="*80)