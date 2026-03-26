import yfinance as yf
import pandas as pd
import numpy as np

ticker = "AAPL"
data = yf.download(ticker, start="2020-01-01", end="2026-03-27", group_by='ticker')

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.droplevel(0)

print("\n" + "="*80)
print("BREAKOUT STRATEGY - APPLE")
print("="*80)

# Calcular máximo móvil (ventana de 52 semanas = ~252 días trading)
lookback = 252  # 52 semanas
data['Max_52w'] = data['Close'].rolling(window=lookback).max()

# Detectar breakout: precio actual > máximo de las últimas 52 semanas
data['Is_Breakout'] = data['Close'] > data['Max_52w'].shift(1)

# Estado actual
print("\nIndicadores actuales:")
print(f"Precio actual: ${data['Close'].iloc[-1]:.2f}")
print(f"Máximo 52 semanas: ${data['Max_52w'].iloc[-1]:.2f}")

if data['Close'].iloc[-1] > data['Max_52w'].iloc[-2]:
    print("\n🚀 BREAKOUT DETECTADO - El precio está en máximo histórico")
    print("   → SEÑAL: COMPRAR")
else:
    diferencia_pct = ((data['Max_52w'].iloc[-2] - data['Close'].iloc[-1]) / data['Close'].iloc[-1]) * 100
    print(f"\n⏳ Sin breakout - Precio está {diferencia_pct:.1f}% por debajo del máximo")
    print("   → SEÑAL: ESPERAR")

# BACKTESTING
print("\n" + "="*80)
print("BACKTESTING - BREAKOUT vs BUY AND HOLD")
print("="*80)

# ESTRATEGIA 1: BREAKOUT
capital = 10000.0
shares = 0.0
operaciones = []
stop_loss_pct = 5  # Stop loss del 5%

for i in range(lookback + 1, len(data)):
    precio = data['Close'].iloc[i]
    is_breakout = data['Is_Breakout'].iloc[i]
    
    # Si no estamos invertidos, buscar breakout
    if shares == 0:
        if is_breakout:
            shares = capital / precio
            precio_compra = precio
            fecha_compra = data.index[i]
            stop_loss_precio = precio * (1 - stop_loss_pct / 100)
    
    # Si estamos invertidos, verificar stop loss o nueva señal de venta
    else:
        # Stop loss activado
        if precio <= stop_loss_precio:
            capital = shares * precio
            ganancia = capital - 10000
            
            operaciones.append({
                'fecha_compra': fecha_compra,
                'precio_compra': precio_compra,
                'fecha_venta': data.index[i],
                'precio_venta': precio,
                'ganancia': ganancia,
                'retorno': (precio / precio_compra - 1) * 100,
                'motivo': 'Stop Loss'
            })
            
            shares = 0
            capital = 10000
        
        # Precio cayó más del 10% desde máximo (trailing stop)
        elif precio < precio_compra * 0.90:
            capital = shares * precio
            ganancia = capital - 10000
            
            operaciones.append({
                'fecha_compra': fecha_compra,
                'precio_compra': precio_compra,
                'fecha_venta': data.index[i],
                'precio_venta': precio,
                'ganancia': ganancia,
                'retorno': (precio / precio_compra - 1) * 100,
                'motivo': 'Trailing Stop'
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
        'retorno': (precio_final / precio_compra - 1) * 100,
        'motivo': 'Venta Final'
    })

capital_breakout = capital if shares == 0 else shares * data['Close'].iloc[-1]
retorno_breakout = ((capital_breakout / 10000) - 1) * 100

# Buy and Hold
precio_inicial = data['Close'].iloc[lookback]
precio_final = data['Close'].iloc[-1]
capital_bh = 10000 * (precio_final / precio_inicial)
retorno_bh = ((capital_bh / 10000) - 1) * 100

# RESULTADOS
print(f"\nBREAKOUT:")
print(f"  Capital final: ${int(capital_breakout):,}")
print(f"  Retorno: {retorno_breakout:+.2f}%")
print(f"  Operaciones: {len(operaciones)}")

if operaciones:
    ganancias = [op['ganancia'] for op in operaciones if op['ganancia'] > 0]
    perdidas = [op['ganancia'] for op in operaciones if op['ganancia'] <= 0]
    
    win_rate = len(ganancias) / len(operaciones) * 100 if operaciones else 0
    print(f"  Win rate: {win_rate:.1f}%")
    
    stop_losses = len([op for op in operaciones if op['motivo'] == 'Stop Loss'])
    trailing_stops = len([op for op in operaciones if op['motivo'] == 'Trailing Stop'])
    print(f"  Stop Loss activados: {stop_losses}")
    print(f"  Trailing Stop activados: {trailing_stops}")
    
    if ganancias:
        print(f"  Ganancia promedio: ${np.mean(ganancias):,.0f}")
    if perdidas:
        print(f"  Pérdida promedio: ${abs(np.mean(perdidas)):,.0f}")

print(f"\nBUY AND HOLD:")
print(f"  Capital final: ${int(capital_bh):,}")
print(f"  Retorno: {retorno_bh:+.2f}%")

# Comparación
ventaja = retorno_breakout - retorno_bh

print("\n" + "="*80)
print("COMPARACIÓN")
print("="*80)

print(f"\nBreakout vs Buy and Hold: {ventaja:+.2f}%")
if ventaja > 0:
    print("  → Breakout GANÓ ✅")
else:
    print("  → Buy and Hold GANÓ ❌")

# Ranking con todas las estrategias anteriores
print("\n" + "="*80)
print("RANKING: BREAKOUT vs TODAS LAS ESTRATEGIAS")
print("="*80)

estrategias = [
    ("Buy and Hold", 245.0),  # Del Mes 1
    ("Trend Following (MA)", 100.0),  # Del Mes 1
    ("MA + SL/TP", 6.0),  # Del Mes 1
    ("Mean Reversion", 0.61),  # Día 26
    ("Momentum", 0.0),  # Día 27
    ("Pair Trading", 0.0),  # Día 28
    ("Breakout", retorno_breakout)  # HOY
]

estrategias_ordenadas = sorted(estrategias, key=lambda x: x[1], reverse=True)

for i, (nombre, retorno) in enumerate(estrategias_ordenadas, 1):
    if i == 1:
        emoji = "🥇"
    elif i == 2:
        emoji = "🥈"
    elif i == 3:
        emoji = "🥉"
    else:
        emoji = f"{i}️⃣"
    
    print(f"{emoji} {nombre}: {retorno:+.2f}%")

# Mostrar algunas operaciones
if operaciones:
    print("\n" + "="*80)
    print("OPERACIONES DE BREAKOUT (primeras 5)")
    print("="*80)
    
    for i, op in enumerate(operaciones[:5], 1):
        print(f"\nOperación {i}:")
        print(f"  Compra: {op['fecha_compra'].strftime('%Y-%m-%d')} a ${op['precio_compra']:.2f}")
        print(f"  Venta: {op['fecha_venta'].strftime('%Y-%m-%d')} a ${op['precio_venta']:.2f}")
        print(f"  Retorno: {op['retorno']:+.2f}%")
        print(f"  Ganancia: ${op['ganancia']:+,.0f}")
        print(f"  Motivo: {op['motivo']}")

    # Mejor y peor operación
    mejor = max(operaciones, key=lambda x: x['ganancia'])
    peor = min(operaciones, key=lambda x: x['ganancia'])
    
    print("\n" + "="*80)
    print("MEJOR Y PEOR OPERACIÓN")
    print("="*80)
    
    print(f"\nMEJOR:")
    print(f"  Ganancia: ${mejor['ganancia']:+,.0f}")
    print(f"  Retorno: {mejor['retorno']:+.2f}%")
    print(f"  Período: {mejor['fecha_compra'].strftime('%Y-%m-%d')} → {mejor['fecha_venta'].strftime('%Y-%m-%d')}")
    
    print(f"\nPEOR:")
    print(f"  Ganancia: ${peor['ganancia']:+,.0f}")
    print(f"  Retorno: {peor['retorno']:+.2f}%")
    print(f"  Período: {peor['fecha_compra'].strftime('%Y-%m-%d')} → {peor['fecha_venta'].strftime('%Y-%m-%d')}")

print("\n" + "="*80)