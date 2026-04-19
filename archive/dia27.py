import yfinance as yf
import pandas as pd
import numpy as np

ticker = "AAPL"
data = yf.download(ticker, start="2020-01-01", end="2026-03-25", group_by='ticker')

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.droplevel(0)

print("\n" + "="*80)
print("MOMENTUM STRATEGY - APPLE")
print("="*80)

# Calcular indicadores de momentum
data['MA200'] = data['Close'].rolling(window=200).mean()

# Momentum: Retorno de los últimos 60 días (3 meses)
data['Momentum_60d'] = data['Close'].pct_change(60) * 100

# RSI
def calcular_rsi(data, periodo=14):
    delta = data['Close'].diff()
    ganancia = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
    perdida = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()
    rs = ganancia / perdida
    rsi = 100 - (100 / (1 + rs))
    return rsi

data['RSI'] = calcular_rsi(data)

# Estado actual
print("\nIndicadores actuales:")
print(f"Precio actual: ${data['Close'].iloc[-1]:.2f}")
print(f"MA200: ${data['MA200'].iloc[-1]:.2f}")
print(f"Momentum 60d: {data['Momentum_60d'].iloc[-1]:+.2f}%")
print(f"RSI: {data['RSI'].iloc[-1]:.2f}")

# Señal actual
precio_actual = data['Close'].iloc[-1]
ma200_actual = data['MA200'].iloc[-1]
momentum_actual = data['Momentum_60d'].iloc[-1]
rsi_actual = data['RSI'].iloc[-1]

print("\nAnálisis de señal:")
print(f"  Precio > MA200: {'✅ SÍ' if precio_actual > ma200_actual else '❌ NO'}")
print(f"  Momentum positivo: {'✅ SÍ' if momentum_actual > 0 else '❌ NO'}")
print(f"  RSI alcista (50-70): {'✅ SÍ' if 50 < rsi_actual < 70 else '❌ NO'}")

if precio_actual > ma200_actual and momentum_actual > 5 and 50 < rsi_actual < 70:
    print("\n🚀 SEÑAL: MOMENTUM ALCISTA - COMPRAR")
elif precio_actual < ma200_actual or momentum_actual < 0:
    print("\n⚠️ SEÑAL: MOMENTUM DÉBIL - VENDER o NO OPERAR")
else:
    print("\n➖ SEÑAL: NEUTRAL")

# BACKTESTING
print("\n" + "="*80)
print("BACKTESTING - MOMENTUM vs MEAN REVERSION vs BUY AND HOLD")
print("="*80)

# ESTRATEGIA 1: MOMENTUM
capital_momentum = 10000.0
shares_momentum = 0.0
operaciones_momentum = []

for i in range(200, len(data)):
    precio = data['Close'].iloc[i]
    ma200 = data['MA200'].iloc[i]
    momentum = data['Momentum_60d'].iloc[i]
    rsi = data['RSI'].iloc[i]
    
    # COMPRAR: Precio > MA200, Momentum > 5%, RSI entre 50-70
    if shares_momentum == 0:
        if precio > ma200 and momentum > 5 and 50 < rsi < 70:
            shares_momentum = capital_momentum / precio
            precio_compra_mom = precio
            fecha_compra_mom = data.index[i]
    
    # VENDER: Momentum negativo o precio < MA200
    else:
        if momentum < 0 or precio < ma200:
            capital_momentum = shares_momentum * precio
            ganancia = capital_momentum - 10000
            
            operaciones_momentum.append({
                'fecha_compra': fecha_compra_mom,
                'precio_compra': precio_compra_mom,
                'fecha_venta': data.index[i],
                'precio_venta': precio,
                'ganancia': ganancia,
                'retorno': (precio / precio_compra_mom - 1) * 100
            })
            
            shares_momentum = 0
            capital_momentum = 10000

# Venta final
if shares_momentum > 0:
    precio_final = data['Close'].iloc[-1]
    capital_momentum = shares_momentum * precio_final
    ganancia = capital_momentum - 10000
    
    operaciones_momentum.append({
        'fecha_compra': fecha_compra_mom,
        'precio_compra': precio_compra_mom,
        'fecha_venta': data.index[-1],
        'precio_venta': precio_final,
        'ganancia': ganancia,
        'retorno': (precio_final / precio_compra_mom - 1) * 100
    })

capital_final_momentum = capital_momentum if shares_momentum == 0 else shares_momentum * data['Close'].iloc[-1]
retorno_momentum = ((capital_final_momentum / 10000) - 1) * 100

# ESTRATEGIA 2: MEAN REVERSION (del día anterior)
data['MA20'] = data['Close'].rolling(window=20).mean()
data['STD20'] = data['Close'].rolling(window=20).std()
data['Z_Score'] = (data['Close'] - data['MA20']) / data['STD20']

capital_mr = 10000.0
shares_mr = 0.0
operaciones_mr = 0

for i in range(200, len(data)):
    precio = data['Close'].iloc[i]
    z_score = data['Z_Score'].iloc[i]
    
    if z_score < -2 and shares_mr == 0:
        shares_mr = capital_mr / precio
    elif z_score > 0 and shares_mr > 0:
        capital_mr = shares_mr * precio
        shares_mr = 0
        capital_mr = 10000
        operaciones_mr += 1

capital_final_mr = capital_mr if shares_mr == 0 else shares_mr * data['Close'].iloc[-1]
retorno_mr = ((capital_final_mr / 10000) - 1) * 100

# Buy and Hold
precio_inicial = data['Close'].iloc[200]
precio_final = data['Close'].iloc[-1]
capital_bh = 10000 * (precio_final / precio_inicial)
retorno_bh = ((capital_bh / 10000) - 1) * 100

# RESULTADOS
print(f"\n1. MOMENTUM:")
print(f"   Capital final: ${int(capital_final_momentum):,}")
print(f"   Retorno: {retorno_momentum:+.2f}%")
print(f"   Operaciones: {len(operaciones_momentum)}")

if operaciones_momentum:
    ganancias = [op['ganancia'] for op in operaciones_momentum if op['ganancia'] > 0]
    perdidas = [op['ganancia'] for op in operaciones_momentum if op['ganancia'] <= 0]
    win_rate = len(ganancias) / len(operaciones_momentum) * 100
    print(f"   Win rate: {win_rate:.1f}%")

print(f"\n2. MEAN REVERSION:")
print(f"   Capital final: ${int(capital_final_mr):,}")
print(f"   Retorno: {retorno_mr:+.2f}%")
print(f"   Operaciones: {operaciones_mr}")

print(f"\n3. BUY AND HOLD:")
print(f"   Capital final: ${int(capital_bh):,}")
print(f"   Retorno: {retorno_bh:+.2f}%")

# Comparaciones
print("\n" + "="*80)
print("COMPARACIÓN DE ESTRATEGIAS")
print("="*80)

ventaja_momentum_vs_bh = retorno_momentum - retorno_bh
ventaja_momentum_vs_mr = retorno_momentum - retorno_mr

print(f"\nMomentum vs Buy and Hold: {ventaja_momentum_vs_bh:+.2f}%")
if ventaja_momentum_vs_bh > 0:
    print("  → Momentum GANÓ ✅")
else:
    print("  → Buy and Hold GANÓ ❌")

print(f"\nMomentum vs Mean Reversion: {ventaja_momentum_vs_mr:+.2f}%")
if ventaja_momentum_vs_mr > 0:
    print("  → Momentum GANÓ ✅")
else:
    print("  → Mean Reversion GANÓ ❌")

# Ranking
estrategias = [
    ("Buy and Hold", retorno_bh),
    ("Momentum", retorno_momentum),
    ("Mean Reversion", retorno_mr)
]
estrategias_ordenadas = sorted(estrategias, key=lambda x: x[1], reverse=True)

print("\n" + "="*80)
print("RANKING FINAL")
print("="*80)

for i, (nombre, retorno) in enumerate(estrategias_ordenadas, 1):
    emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
    print(f"{emoji} {i}. {nombre}: {retorno:+.2f}%")

# Mostrar algunas operaciones de Momentum
if operaciones_momentum:
    print("\n" + "="*80)
    print("OPERACIONES DE MOMENTUM (primeras 5)")
    print("="*80)
    
    for i, op in enumerate(operaciones_momentum[:5], 1):
        print(f"\nOperación {i}:")
        print(f"  Compra: {op['fecha_compra'].strftime('%Y-%m-%d')} a ${op['precio_compra']:.2f}")
        print(f"  Venta: {op['fecha_venta'].strftime('%Y-%m-%d')} a ${op['precio_venta']:.2f}")
        print(f"  Retorno: {op['retorno']:+.2f}%")
        print(f"  Ganancia: ${op['ganancia']:+,.0f}")

print("\n" + "="*80)