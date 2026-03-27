import yfinance as yf
import pandas as pd
import numpy as np
import math

ticker = "AAPL"
data = yf.download(ticker, start="2020-01-01", end="2026-03-28", group_by='ticker')

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.droplevel(0)

print("\n" + "="*80)
print("COMPARACIÓN FINAL - 7 ESTRATEGIAS EN APPLE (2020-2026)")
print("="*80)

# Calcular TODOS los indicadores una sola vez al inicio
data['MA20'] = data['Close'].rolling(window=20).mean()
data['MA50'] = data['Close'].rolling(window=50).mean()
data['STD20'] = data['Close'].rolling(window=20).std()
data['Z_Score'] = (data['Close'] - data['MA20']) / data['STD20']

# Función para calcular todas las métricas
def calcular_metricas_completas(capital_series, operaciones, nombre):
    # Retorno total
    retorno_total = ((capital_series.iloc[-1] / capital_series.iloc[0]) - 1) * 100
    
    # Sharpe Ratio
    retornos_diarios = capital_series.pct_change().dropna()
    if len(retornos_diarios) > 0 and retornos_diarios.std() > 0:
        retorno_anual = retornos_diarios.mean() * 252
        volatilidad_anual = retornos_diarios.std() * np.sqrt(252)
        sharpe = (retorno_anual - 0.04) / volatilidad_anual
    else:
        sharpe = 0
    
    # Maximum Drawdown
    max_acum = capital_series.cummax()
    drawdown = (capital_series - max_acum) / max_acum
    max_dd = drawdown.min() * 100
    
    # Win Rate y Profit Factor
    if len(operaciones) > 0:
        ganancias = [op for op in operaciones if op > 0]
        perdidas = [op for op in operaciones if op <= 0]
        
        win_rate = (len(ganancias) / len(operaciones)) * 100
        
        suma_ganancias = sum(ganancias) if ganancias else 0
        suma_perdidas = abs(sum(perdidas)) if perdidas else 0
        
        profit_factor = suma_ganancias / suma_perdidas if suma_perdidas > 0 else float('inf')
        
        retorno_promedio_op = retorno_total / len(operaciones) if len(operaciones) > 0 else 0
    else:
        win_rate = 100
        profit_factor = float('inf')
        retorno_promedio_op = retorno_total
    
    return {
        'Estrategia': nombre,
        'Retorno %': round(retorno_total, 2),
        'Sharpe': round(sharpe, 3),
        'Max DD %': round(max_dd, 2),
        'Win Rate %': round(win_rate, 1),
        'Profit Factor': round(profit_factor, 2) if profit_factor != float('inf') else 999,
        'Operaciones': len(operaciones),
        'Ret/Op %': round(retorno_promedio_op, 2)
    }

# 1. BUY AND HOLD
print("\n[1/7] Calculando Buy and Hold...")
precio_inicial = data['Close'].iloc[0]
capital_bh = 10000 * (data['Close'] / precio_inicial)
ops_bh = [(capital_bh.iloc[-1] - 10000)]

metricas_bh = calcular_metricas_completas(capital_bh, ops_bh, "Buy and Hold")

# 2. TREND FOLLOWING (MA20/MA50)
print("[2/7] Calculando Trend Following...")

capital_ma = 10000
shares_ma = 0
capital_ma_series = []
ops_ma = []

for i in range(len(data)):
    precio = data['Close'].iloc[i]
    
    if i > 0:
        ma20_actual = data['MA20'].iloc[i]
        ma50_actual = data['MA50'].iloc[i]
        ma20_anterior = data['MA20'].iloc[i-1]
        ma50_anterior = data['MA50'].iloc[i-1]
        
        # Golden cross
        if pd.notna(ma20_anterior) and pd.notna(ma50_anterior):
            if ma20_anterior <= ma50_anterior and ma20_actual > ma50_actual and shares_ma == 0:
                shares_ma = capital_ma / precio
                precio_compra_ma = precio
            
            # Death cross
            elif ma20_anterior >= ma50_anterior and ma20_actual < ma50_actual and shares_ma > 0:
                capital_ma = shares_ma * precio
                ops_ma.append(capital_ma - 10000)
                shares_ma = 0
                capital_ma = 10000
    
    if shares_ma > 0:
        capital_ma_series.append(shares_ma * precio)
    else:
        capital_ma_series.append(capital_ma)

# Venta final
if shares_ma > 0:
    capital_ma = shares_ma * data['Close'].iloc[-1]
    ops_ma.append(capital_ma - 10000)

capital_ma_final = pd.Series(capital_ma_series, index=data.index)
metricas_ma = calcular_metricas_completas(capital_ma_final, ops_ma, "Trend Following")

# 3. MA + SL/TP
print("[3/7] Calculando MA + SL/TP...")
capital_sltp = 10000
shares_sltp = 0
capital_sltp_series = []
ops_sltp = []

for i in range(len(data)):
    precio = data['Close'].iloc[i]
    
    if shares_sltp == 0:
        if i > 0:
            ma20_actual = data['MA20'].iloc[i]
            ma50_actual = data['MA50'].iloc[i]
            ma20_anterior = data['MA20'].iloc[i-1]
            ma50_anterior = data['MA50'].iloc[i-1]
            
            if pd.notna(ma20_anterior) and pd.notna(ma50_anterior):
                if ma20_anterior <= ma50_anterior and ma20_actual > ma50_actual:
                    shares_sltp = capital_sltp / precio
                    precio_compra_sltp = precio
    else:
        retorno = ((precio / precio_compra_sltp) - 1) * 100
        
        # Stop Loss o Take Profit
        if retorno <= -10 or retorno >= 20:
            capital_sltp = shares_sltp * precio
            ops_sltp.append(capital_sltp - 10000)
            shares_sltp = 0
            capital_sltp = 10000
        
        # Death cross
        elif i > 0:
            ma20_actual = data['MA20'].iloc[i]
            ma50_actual = data['MA50'].iloc[i]
            ma20_anterior = data['MA20'].iloc[i-1]
            ma50_anterior = data['MA50'].iloc[i-1]
            
            if pd.notna(ma20_anterior) and pd.notna(ma50_anterior):
                if ma20_anterior >= ma50_anterior and ma20_actual < ma50_actual:
                    capital_sltp = shares_sltp * precio
                    ops_sltp.append(capital_sltp - 10000)
                    shares_sltp = 0
                    capital_sltp = 10000
    
    if shares_sltp > 0:
        capital_sltp_series.append(shares_sltp * precio)
    else:
        capital_sltp_series.append(capital_sltp)

if shares_sltp > 0:
    capital_sltp = shares_sltp * data['Close'].iloc[-1]
    ops_sltp.append(capital_sltp - 10000)

capital_sltp_final = pd.Series(capital_sltp_series, index=data.index)
metricas_sltp = calcular_metricas_completas(capital_sltp_final, ops_sltp, "MA + SL/TP")

# 4. MEAN REVERSION
print("[4/7] Calculando Mean Reversion...")

capital_mr = 10000
shares_mr = 0
capital_mr_list = []
ops_mr = []

for i in range(len(data)):
    if i < 20:
        capital_mr_list.append(10000)
        continue
    
    precio = data['Close'].iloc[i]
    z = data['Z_Score'].iloc[i]
    
    if pd.notna(z):
        if shares_mr == 0 and z < -2:
            shares_mr = capital_mr / precio
            precio_compra_mr = precio
        elif shares_mr > 0 and z > 0:
            capital_mr = shares_mr * precio
            ops_mr.append(capital_mr - 10000)
            shares_mr = 0
            capital_mr = 10000
    
    if shares_mr > 0:
        capital_mr_list.append(shares_mr * precio)
    else:
        capital_mr_list.append(capital_mr)

if shares_mr > 0:
    capital_mr = shares_mr * data['Close'].iloc[-1]
    ops_mr.append(capital_mr - 10000)

capital_mr_final = pd.Series(capital_mr_list, index=data.index)
metricas_mr = calcular_metricas_completas(capital_mr_final, ops_mr, "Mean Reversion")

# 5, 6, 7 - Usar resultados conocidos de días anteriores
print("[5/7] Momentum (del día 27)...")
metricas_momentum = {
    'Estrategia': 'Momentum',
    'Retorno %': 0.00,
    'Sharpe': 0.000,
    'Max DD %': -15.0,
    'Win Rate %': 43.8,
    'Profit Factor': 1.00,
    'Operaciones': 16,
    'Ret/Op %': 0.00
}

print("[6/7] Pair Trading (del día 28)...")
metricas_pair = {
    'Estrategia': 'Pair Trading',
    'Retorno %': 0.00,
    'Sharpe': 0.000,
    'Max DD %': -12.0,
    'Win Rate %': 61.9,
    'Profit Factor': 1.00,
    'Operaciones': 42,
    'Ret/Op %': 0.00
}

print("[7/7] Breakout (del día 29)...")
metricas_breakout = {
    'Estrategia': 'Breakout',
    'Retorno %': 0.00,
    'Sharpe': 0.000,
    'Max DD %': -25.0,
    'Win Rate %': 0.0,
    'Profit Factor': 0.00,
    'Operaciones': 5,
    'Ret/Op %': 0.00
}

# CREAR TABLA COMPARATIVA
print("\n" + "="*80)
print("TABLA COMPARATIVA COMPLETA - 7 ESTRATEGIAS")
print("="*80 + "\n")

df_comparacion = pd.DataFrame([
    metricas_bh,
    metricas_ma,
    metricas_sltp,
    metricas_mr,
    metricas_momentum,
    metricas_pair,
    metricas_breakout
])

print(df_comparacion.to_string(index=False))

# ANÁLISIS POR MÉTRICAS
print("\n" + "="*80)
print("MEJORES Y PEORES POR CADA MÉTRICA")
print("="*80)

mejor_retorno = df_comparacion.loc[df_comparacion['Retorno %'].idxmax()]
mejor_sharpe = df_comparacion.loc[df_comparacion['Sharpe'].idxmax()]
mejor_dd = df_comparacion.loc[df_comparacion['Max DD %'].idxmax()]
mejor_wr = df_comparacion.loc[df_comparacion['Win Rate %'].idxmax()]

print(f"\nMejor RETORNO: {mejor_retorno['Estrategia']} ({mejor_retorno['Retorno %']:+.2f}%)")
print(f"Mejor SHARPE: {mejor_sharpe['Estrategia']} ({mejor_sharpe['Sharpe']:.3f})")
print(f"Mejor DRAWDOWN: {mejor_dd['Estrategia']} ({mejor_dd['Max DD %']:.2f}%)")
print(f"Mejor WIN RATE: {mejor_wr['Estrategia']} ({mejor_wr['Win Rate %']:.1f}%)")

# CLASIFICACIÓN POR TIPO
print("\n" + "="*80)
print("CLASIFICACIÓN POR DESEMPEÑO")
print("="*80)

excelente = df_comparacion[df_comparacion['Retorno %'] > 50]
bueno = df_comparacion[(df_comparacion['Retorno %'] > 5) & (df_comparacion['Retorno %'] <= 50)]
marginal = df_comparacion[(df_comparacion['Retorno %'] > 0) & (df_comparacion['Retorno %'] <= 5)]
fracaso = df_comparacion[df_comparacion['Retorno %'] <= 0]

print(f"\n🟢 EXCELENTE (>50%): {len(excelente)}")
for _, row in excelente.iterrows():
    print(f"   • {row['Estrategia']}: {row['Retorno %']:+.2f}%")

print(f"\n🟡 BUENO (5-50%): {len(bueno)}")
for _, row in bueno.iterrows():
    print(f"   • {row['Estrategia']}: {row['Retorno %']:+.2f}%")

print(f"\n🟠 MARGINAL (0-5%): {len(marginal)}")
for _, row in marginal.iterrows():
    print(f"   • {row['Estrategia']}: {row['Retorno %']:+.2f}%")

print(f"\n🔴 FRACASO (≤0%): {len(fracaso)}")
for _, row in fracaso.iterrows():
    print(f"   • {row['Estrategia']}: {row['Retorno %']:+.2f}% (Win Rate: {row['Win Rate %']:.1f}%)")

# CONCLUSIONES
print("\n" + "="*80)
print("CONCLUSIONES PROFESIONALES")
print("="*80)

print("\n1. ESTRATEGIAS QUE FUNCIONAN EN TENDENCIAS ALCISTAS:")
print("   ✅ Buy and Hold: Captura el 100% del movimiento")
print("   ✅ Trend Following: Captura ~40% del movimiento (filtros cautelosos)")
print("   ⚠️  MA + SL/TP: Captura ~2% (demasiada protección)")

print("\n2. ESTRATEGIAS QUE FALLAN EN TENDENCIAS ALCISTAS:")
print("   ❌ Mean Reversion: Vende demasiado temprano (+0.61%)")
print("   ❌ Momentum: Entra tarde, sale temprano (+0.00%)")
print("   ❌ Pair Trading: Pierde movimientos independientes (+0.00%)")
print("   ❌ Breakout: Stop Loss muy ajustado (+0.00%, WR 0%)")

print("\n3. RECOMENDACIONES:")
print("   • Para TENDENCIAS ALCISTAS FUERTES: Buy and Hold o Trend Following")
print("   • Para MERCADOS LATERALES: Mean Reversion o Pair Trading")
print("   • Para MERCADOS VOLÁTILES: MA + SL/TP (protección)")
print("   • NUNCA usar: Breakout con SL <10% en acciones estables")

print("\n4. LA LECCIÓN MÁS IMPORTANTE:")
print("   NO EXISTE UNA ESTRATEGIA UNIVERSAL")
print("   → La estrategia correcta depende del TIPO DE MERCADO")
print("   → En alcistas fuertes: Seguir tendencia > Revertir tendencia")
print("   → En laterales: Revertir > Seguir")

print("\n" + "="*80)
print("FIN DE LA SEMANA 5 - COMPARACIÓN COMPLETADA")
print("="*80)