import yfinance as yf
import pandas as pd
import numpy as np

ticker = "AAPL"
data = yf.download(ticker, start="2020-01-01", end="2026-03-31", group_by='ticker')

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.droplevel(0)

print("\n" + "="*80)
print("POSITION SIZING Y KELLY CRITERION - APPLE")
print("="*80)

# Calcular indicadores
data['MA20'] = data['Close'].rolling(window=20).mean()
data['MA50'] = data['Close'].rolling(window=50).mean()

# BACKTESTING CON DIFERENTES TAMAÑOS DE POSICIÓN
def backtest_con_position_sizing(data, position_size_pct):
    """
    position_size_pct: % del capital a invertir en cada operación (0-100)
    """
    capital = 10000.0
    operaciones = []
    
    in_position = False
    shares = 0
    
    for i in range(1, len(data)):
        if pd.isna(data['MA20'].iloc[i]) or pd.isna(data['MA50'].iloc[i]):
            continue
        
        precio = data['Close'].iloc[i]
        ma20_actual = data['MA20'].iloc[i]
        ma50_actual = data['MA50'].iloc[i]
        ma20_anterior = data['MA20'].iloc[i-1]
        ma50_anterior = data['MA50'].iloc[i-1]
        
        # Golden cross
        if not in_position and ma20_anterior <= ma50_anterior and ma20_actual > ma50_actual:
            # Invertir solo position_size_pct del capital
            capital_a_invertir = capital * (position_size_pct / 100)
            shares = capital_a_invertir / precio
            precio_compra = precio
            fecha_compra = data.index[i]
            in_position = True
        
        # Death cross
        elif in_position and ma20_anterior >= ma50_anterior and ma20_actual < ma50_actual:
            capital_operacion = shares * precio
            ganancia = capital_operacion - (capital * (position_size_pct / 100))
            
            # Actualizar capital total
            capital = capital + ganancia
            
            operaciones.append({
                'fecha_compra': fecha_compra,
                'precio_compra': precio_compra,
                'fecha_venta': data.index[i],
                'precio_venta': precio,
                'ganancia': ganancia,
                'retorno_op': (precio / precio_compra - 1) * 100
            })
            
            in_position = False
            shares = 0
    
    # Venta final
    if in_position:
        precio_final = data['Close'].iloc[-1]
        capital_operacion = shares * precio_final
        ganancia = capital_operacion - (10000 * (position_size_pct / 100))
        capital = capital + ganancia
        
        operaciones.append({
            'fecha_compra': fecha_compra,
            'precio_compra': precio_compra,
            'fecha_venta': data.index[-1],
            'precio_venta': precio_final,
            'ganancia': ganancia,
            'retorno_op': (precio_final / precio_compra - 1) * 100
        })
    
    return capital, operaciones

# Calcular métricas de la estrategia
print("\n" + "="*80)
print("CALCULANDO MÉTRICAS DE LA ESTRATEGIA")
print("="*80)

# Primero con 100% para obtener métricas
capital_100, ops_100 = backtest_con_position_sizing(data, 100)

if ops_100:
    ganancias = [op['ganancia'] for op in ops_100 if op['ganancia'] > 0]
    perdidas = [op['ganancia'] for op in ops_100 if op['ganancia'] <= 0]
    
    win_rate = len(ganancias) / len(ops_100)
    
    avg_win = np.mean(ganancias) if ganancias else 0
    avg_loss = abs(np.mean(perdidas)) if perdidas else 0
    
    print(f"\nMétricas de la estrategia Trend Following:")
    print(f"  Operaciones: {len(ops_100)}")
    print(f"  Win Rate: {win_rate*100:.1f}%")
    print(f"  Ganancia promedio: ${avg_win:,.0f}")
    print(f"  Pérdida promedio: ${avg_loss:,.0f}")
    
    # CALCULAR KELLY CRITERION
    if avg_loss > 0:
        ratio_win_loss = avg_win / avg_loss
        kelly_pct = win_rate - ((1 - win_rate) / ratio_win_loss)
        kelly_pct = max(0, kelly_pct)  # No puede ser negativo
        
        print("\n" + "="*80)
        print("KELLY CRITERION")
        print("="*80)
        
        print(f"\nFórmula Kelly:")
        print(f"  Kelly % = Win Rate - [(1 - Win Rate) / (Avg Win / Avg Loss)]")
        print(f"  Kelly % = {win_rate:.3f} - [(1 - {win_rate:.3f}) / {ratio_win_loss:.3f}]")
        print(f"  Kelly % = {kelly_pct:.3f} = {kelly_pct*100:.1f}%")
        
        half_kelly = kelly_pct * 0.5
        quarter_kelly = kelly_pct * 0.25
        
        print(f"\n  Full Kelly: {kelly_pct*100:.1f}% (MUY agresivo)")
        print(f"  Half Kelly: {half_kelly*100:.1f}% (recomendado)")
        print(f"  Quarter Kelly: {quarter_kelly*100:.1f}% (conservador)")
    else:
        print("\n⚠️ No hay pérdidas en la estrategia, no se puede calcular Kelly")
        kelly_pct = 0.5
        half_kelly = 0.25
        quarter_kelly = 0.125

# COMPARAR DIFERENTES TAMAÑOS DE POSICIÓN
print("\n" + "="*80)
print("COMPARACIÓN: DIFERENTES TAMAÑOS DE POSICIÓN")
print("="*80)

position_sizes = [
    ("100% (All-in)", 100),
    (f"Full Kelly ({kelly_pct*100:.1f}%)", kelly_pct*100),
    (f"Half Kelly ({half_kelly*100:.1f}%)", half_kelly*100),
    (f"Quarter Kelly ({quarter_kelly*100:.1f}%)", quarter_kelly*100),
    ("50% (Moderado)", 50),
    ("25% (Conservador)", 25),
    ("10% (Muy conservador)", 10)
]

resultados = []

for nombre, size in position_sizes:
    capital_final, ops = backtest_con_position_sizing(data, size)
    retorno = ((capital_final / 10000) - 1) * 100
    
    # Calcular volatilidad del capital (drawdown aprox)
    # Esto es simplificado, idealmente calcularíamos capital diario
    
    resultados.append({
        'Estrategia': nombre,
        'Position Size %': size,
        'Capital Final': int(capital_final),
        'Retorno %': round(retorno, 2),
        'Operaciones': len(ops)
    })

df_resultados = pd.DataFrame(resultados)

print("\n")
print(df_resultados.to_string(index=False))

# Encontrar el mejor
mejor = df_resultados.loc[df_resultados['Retorno %'].idxmax()]

print("\n" + "="*80)
print("ANÁLISIS")
print("="*80)

print(f"\nMejor estrategia: {mejor['Estrategia']}")
print(f"  Retorno: {mejor['Retorno %']:+.2f}%")
print(f"  Capital final: ${mejor['Capital Final']:,}")

print("\n" + "="*80)
print("CONCLUSIONES")
print("="*80)

print("\n1. Full Kelly (100% o Kelly óptimo):")
print("   • Maximiza el crecimiento matemáticamente")
print("   • PERO muy arriesgado en la práctica")
print("   • Una mala racha puede destruir el capital")

print("\n2. Half Kelly (recomendado para profesionales):")
print("   • Balance entre crecimiento y seguridad")
print("   • Usado por hedge funds")
print("   • Reduce volatilidad significativamente")

print("\n3. Quarter Kelly o menos (conservador):")
print("   • Muy seguro pero crece lento")
print("   • Apropiado para capital que NO puedes perder")
print("   • Mejor para principiantes")

print("\n4. LA REGLA DE ORO:")
print("   • NUNCA uses más del 50% de tu capital en una operación")
print("   • Incluso si Kelly dice 80-100%")
print("   • La teoría no considera cisnes negros (eventos imprevistos)")

print("\n" + "="*80)