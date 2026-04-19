import yfinance as yf
import pandas as pd
import numpy as np

# Descargar datos de ambas acciones
print("\n" + "="*80)
print("PAIR TRADING - APPLE vs MICROSOFT")
print("="*80)
print("\nDescargando datos...\n")

aapl = yf.download("AAPL", start="2020-01-01", end="2026-03-26", progress=False, group_by='ticker')
msft = yf.download("MSFT", start="2020-01-01", end="2026-03-26", progress=False, group_by='ticker')

if isinstance(aapl.columns, pd.MultiIndex):
    aapl.columns = aapl.columns.droplevel(0)
if isinstance(msft.columns, pd.MultiIndex):
    msft.columns = msft.columns.droplevel(0)

# Crear DataFrame combinado
data = pd.DataFrame({
    'AAPL': aapl['Close'],
    'MSFT': msft['Close']
})

# Calcular el ratio (spread)
data['Ratio'] = data['AAPL'] / data['MSFT']

# Media móvil del ratio (ventana de 30 días)
window = 30
data['Ratio_MA'] = data['Ratio'].rolling(window=window).mean()
data['Ratio_STD'] = data['Ratio'].rolling(window=window).std()

# Bandas (media ± 2 desviaciones estándar)
data['Upper_Band'] = data['Ratio_MA'] + (2 * data['Ratio_STD'])
data['Lower_Band'] = data['Ratio_MA'] - (2 * data['Ratio_STD'])

# Z-score del ratio
data['Z_Score'] = (data['Ratio'] - data['Ratio_MA']) / data['Ratio_STD']

# Estado actual
print("="*80)
print("ESTADO ACTUAL DEL PAR")
print("="*80)

print(f"\nPrecio AAPL: ${data['AAPL'].iloc[-1]:.2f}")
print(f"Precio MSFT: ${data['MSFT'].iloc[-1]:.2f}")
print(f"Ratio actual: {data['Ratio'].iloc[-1]:.4f}")
print(f"Ratio promedio (30d): {data['Ratio_MA'].iloc[-1]:.4f}")
print(f"Z-Score: {data['Z_Score'].iloc[-1]:.2f}")

# Señal actual
z_actual = data['Z_Score'].iloc[-1]

print("\nInterpretación:")
if z_actual > 2:
    print("  🔴 AAPL está CARA vs MSFT (ratio muy alto)")
    print("  → VENDER AAPL, COMPRAR MSFT")
elif z_actual < -2:
    print("  🟢 AAPL está BARATA vs MSFT (ratio muy bajo)")
    print("  → COMPRAR AAPL, VENDER MSFT")
else:
    print("  ⚪ Ratio NEUTRAL - No operar")

# BACKTESTING
print("\n" + "="*80)
print("BACKTESTING - PAIR TRADING vs BUY AND HOLD")
print("="*80)

# Estrategia Pair Trading
capital = 10000.0
position = None  # None, 'long_aapl', 'long_msft'
operaciones = []

for i in range(window, len(data)):
    z_score = data['Z_Score'].iloc[i]
    
    # Si no hay posición abierta
    if position is None:
        # AAPL barata vs MSFT (Z < -2) → COMPRAR AAPL
        if z_score < -2:
            shares_aapl = capital / data['AAPL'].iloc[i]
            precio_entrada_aapl = data['AAPL'].iloc[i]
            precio_entrada_msft = data['MSFT'].iloc[i]
            fecha_entrada = data.index[i]
            position = 'long_aapl'
        
        # AAPL cara vs MSFT (Z > 2) → COMPRAR MSFT
        elif z_score > 2:
            shares_msft = capital / data['MSFT'].iloc[i]
            precio_entrada_aapl = data['AAPL'].iloc[i]
            precio_entrada_msft = data['MSFT'].iloc[i]
            fecha_entrada = data.index[i]
            position = 'long_msft'
    
    # Si hay posición abierta, verificar salida
    else:
        # Salir cuando el ratio vuelve cerca de la media (Z entre -0.5 y 0.5)
        if -0.5 <= z_score <= 0.5:
            precio_salida_aapl = data['AAPL'].iloc[i]
            precio_salida_msft = data['MSFT'].iloc[i]
            
            if position == 'long_aapl':
                capital = shares_aapl * precio_salida_aapl
                ganancia = capital - 10000
                
                operaciones.append({
                    'tipo': 'Long AAPL',
                    'fecha_entrada': fecha_entrada,
                    'fecha_salida': data.index[i],
                    'aapl_entrada': precio_entrada_aapl,
                    'aapl_salida': precio_salida_aapl,
                    'msft_entrada': precio_entrada_msft,
                    'msft_salida': precio_salida_msft,
                    'ganancia': ganancia
                })
            
            else:  # long_msft
                capital = shares_msft * precio_salida_msft
                ganancia = capital - 10000
                
                operaciones.append({
                    'tipo': 'Long MSFT',
                    'fecha_entrada': fecha_entrada,
                    'fecha_salida': data.index[i],
                    'aapl_entrada': precio_entrada_aapl,
                    'aapl_salida': precio_salida_aapl,
                    'msft_entrada': precio_entrada_msft,
                    'msft_salida': precio_salida_msft,
                    'ganancia': ganancia
                })
            
            position = None
            capital = 10000  # Reset para siguiente operación

# Calcular capital final
if position == 'long_aapl':
    capital_final = shares_aapl * data['AAPL'].iloc[-1]
elif position == 'long_msft':
    capital_final = shares_msft * data['MSFT'].iloc[-1]
else:
    capital_final = capital

retorno_pair = ((capital_final / 10000) - 1) * 100

# Buy and Hold AAPL
precio_inicial_aapl = data['AAPL'].iloc[window]
precio_final_aapl = data['AAPL'].iloc[-1]
capital_bh_aapl = 10000 * (precio_final_aapl / precio_inicial_aapl)
retorno_bh_aapl = ((capital_bh_aapl / 10000) - 1) * 100

# Buy and Hold MSFT
precio_inicial_msft = data['MSFT'].iloc[window]
precio_final_msft = data['MSFT'].iloc[-1]
capital_bh_msft = 10000 * (precio_final_msft / precio_inicial_msft)
retorno_bh_msft = ((capital_bh_msft / 10000) - 1) * 100

# Buy and Hold 50/50 (mitad en cada una)
capital_bh_5050 = (capital_bh_aapl + capital_bh_msft) / 2
retorno_bh_5050 = ((capital_bh_5050 / 10000) - 1) * 100

# RESULTADOS
print(f"\nPAIR TRADING:")
print(f"  Capital final: ${int(capital_final):,}")
print(f"  Retorno: {retorno_pair:+.2f}%")
print(f"  Operaciones: {len(operaciones)}")

if operaciones:
    ganancias = [op['ganancia'] for op in operaciones if op['ganancia'] > 0]
    perdidas = [op['ganancia'] for op in operaciones if op['ganancia'] <= 0]
    
    win_rate = len(ganancias) / len(operaciones) * 100 if operaciones else 0
    print(f"  Win rate: {win_rate:.1f}%")
    
    long_aapl = len([op for op in operaciones if op['tipo'] == 'Long AAPL'])
    long_msft = len([op for op in operaciones if op['tipo'] == 'Long MSFT'])
    print(f"  Operaciones Long AAPL: {long_aapl}")
    print(f"  Operaciones Long MSFT: {long_msft}")

print(f"\nBUY AND HOLD AAPL:")
print(f"  Capital final: ${int(capital_bh_aapl):,}")
print(f"  Retorno: {retorno_bh_aapl:+.2f}%")

print(f"\nBUY AND HOLD MSFT:")
print(f"  Capital final: ${int(capital_bh_msft):,}")
print(f"  Retorno: {retorno_bh_msft:+.2f}%")

print(f"\nBUY AND HOLD 50/50 (AAPL + MSFT):")
print(f"  Capital final: ${int(capital_bh_5050):,}")
print(f"  Retorno: {retorno_bh_5050:+.2f}%")

# Comparaciones
print("\n" + "="*80)
print("COMPARACIÓN")
print("="*80)

ventaja_vs_aapl = retorno_pair - retorno_bh_aapl
ventaja_vs_msft = retorno_pair - retorno_bh_msft
ventaja_vs_5050 = retorno_pair - retorno_bh_5050

print(f"\nPair Trading vs Buy and Hold AAPL: {ventaja_vs_aapl:+.2f}%")
if ventaja_vs_aapl > 0:
    print("  → Pair Trading GANÓ ✅")
else:
    print("  → Buy and Hold AAPL GANÓ ❌")

print(f"\nPair Trading vs Buy and Hold MSFT: {ventaja_vs_msft:+.2f}%")
if ventaja_vs_msft > 0:
    print("  → Pair Trading GANÓ ✅")
else:
    print("  → Buy and Hold MSFT GANÓ ❌")

print(f"\nPair Trading vs Buy and Hold 50/50: {ventaja_vs_5050:+.2f}%")
if ventaja_vs_5050 > 0:
    print("  → Pair Trading GANÓ ✅")
else:
    print("  → Buy and Hold 50/50 GANÓ ❌")

# Ranking
print("\n" + "="*80)
print("RANKING FINAL")
print("="*80)

estrategias = [
    ("Buy and Hold AAPL", retorno_bh_aapl),
    ("Buy and Hold MSFT", retorno_bh_msft),
    ("Buy and Hold 50/50", retorno_bh_5050),
    ("Pair Trading", retorno_pair)
]
estrategias_ordenadas = sorted(estrategias, key=lambda x: x[1], reverse=True)

for i, (nombre, retorno) in enumerate(estrategias_ordenadas, 1):
    emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "4️⃣"
    print(f"{emoji} {i}. {nombre}: {retorno:+.2f}%")

# Mostrar algunas operaciones
if operaciones:
    print("\n" + "="*80)
    print("OPERACIONES DE PAIR TRADING (primeras 5)")
    print("="*80)
    
    for i, op in enumerate(operaciones[:5], 1):
        print(f"\nOperación {i} - {op['tipo']}:")
        print(f"  Entrada: {op['fecha_entrada'].strftime('%Y-%m-%d')}")
        print(f"  AAPL: ${op['aapl_entrada']:.2f} → ${op['aapl_salida']:.2f} ({(op['aapl_salida']/op['aapl_entrada']-1)*100:+.1f}%)")
        print(f"  MSFT: ${op['msft_entrada']:.2f} → ${op['msft_salida']:.2f} ({(op['msft_salida']/op['msft_entrada']-1)*100:+.1f}%)")
        print(f"  Ganancia: ${op['ganancia']:+,.0f}")

print("\n" + "="*80)