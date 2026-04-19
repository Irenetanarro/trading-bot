import yfinance as yf
import pandas as pd
import numpy as np

# Descargar datos de ambas acciones
print("\n" + "="*80)
print("PORTFOLIO REBALANCING DINÁMICO - AAPL + MSFT")
print("="*80)
print("\nDescargando datos...\n")

aapl = yf.download("AAPL", start="2020-01-01", end="2026-04-01", progress=False, group_by='ticker')
msft = yf.download("MSFT", start="2020-01-01", end="2026-04-01", progress=False, group_by='ticker')

if isinstance(aapl.columns, pd.MultiIndex):
    aapl.columns = aapl.columns.droplevel(0)
if isinstance(msft.columns, pd.MultiIndex):
    msft.columns = msft.columns.droplevel(0)

# Combinar en un DataFrame
data = pd.DataFrame({
    'AAPL': aapl['Close'],
    'MSFT': msft['Close']
})

# ESTRATEGIA 1: BUY AND HOLD (Sin rebalanceo)
def buy_and_hold(data, capital_inicial=10000):
    # 50/50 inicial
    shares_aapl = (capital_inicial * 0.5) / data['AAPL'].iloc[0]
    shares_msft = (capital_inicial * 0.5) / data['MSFT'].iloc[0]
    
    capital_series = []
    for i in range(len(data)):
        valor_aapl = shares_aapl * data['AAPL'].iloc[i]
        valor_msft = shares_msft * data['MSFT'].iloc[i]
        capital_total = valor_aapl + valor_msft
        capital_series.append(capital_total)
    
    return pd.Series(capital_series, index=data.index), 0  # 0 rebalanceos

# ESTRATEGIA 2: REBALANCEO PERIÓDICO
def rebalanceo_periodico(data, capital_inicial=10000, frecuencia_dias=90):
    """
    frecuencia_dias: cada cuántos días rebalancear
    90 = trimestral, 180 = semestral, 365 = anual
    """
    shares_aapl = (capital_inicial * 0.5) / data['AAPL'].iloc[0]
    shares_msft = (capital_inicial * 0.5) / data['MSFT'].iloc[0]
    
    capital_series = []
    dias_desde_rebalanceo = 0
    num_rebalanceos = 0
    
    for i in range(len(data)):
        valor_aapl = shares_aapl * data['AAPL'].iloc[i]
        valor_msft = shares_msft * data['MSFT'].iloc[i]
        capital_total = valor_aapl + valor_msft
        
        # Rebalancear si pasaron X días
        if dias_desde_rebalanceo >= frecuencia_dias:
            # Volver a 50/50
            shares_aapl = (capital_total * 0.5) / data['AAPL'].iloc[i]
            shares_msft = (capital_total * 0.5) / data['MSFT'].iloc[i]
            dias_desde_rebalanceo = 0
            num_rebalanceos += 1
        
        capital_series.append(capital_total)
        dias_desde_rebalanceo += 1
    
    return pd.Series(capital_series, index=data.index), num_rebalanceos

# ESTRATEGIA 3: REBALANCEO POR THRESHOLD
def rebalanceo_threshold(data, capital_inicial=10000, threshold=0.10):
    """
    threshold: desviación máxima permitida (ej: 0.10 = 10%)
    Si AAPL > 60% o < 40%, rebalancear
    """
    shares_aapl = (capital_inicial * 0.5) / data['AAPL'].iloc[0]
    shares_msft = (capital_inicial * 0.5) / data['MSFT'].iloc[0]
    
    capital_series = []
    num_rebalanceos = 0
    
    for i in range(len(data)):
        valor_aapl = shares_aapl * data['AAPL'].iloc[i]
        valor_msft = shares_msft * data['MSFT'].iloc[i]
        capital_total = valor_aapl + valor_msft
        
        # Calcular % actual
        pct_aapl = valor_aapl / capital_total
        
        # Rebalancear si se desvía más del threshold
        if abs(pct_aapl - 0.5) > threshold:
            shares_aapl = (capital_total * 0.5) / data['AAPL'].iloc[i]
            shares_msft = (capital_total * 0.5) / data['MSFT'].iloc[i]
            num_rebalanceos += 1
        
        capital_series.append(capital_total)
    
    return pd.Series(capital_series, index=data.index), num_rebalanceos

# EJECUTAR TODAS LAS ESTRATEGIAS
print("="*80)
print("BACKTESTING - DIFERENTES ESTRATEGIAS DE REBALANCEO")
print("="*80)

print("\n[1/7] Buy and Hold (sin rebalanceo)...")
capital_bh, rebal_bh = buy_and_hold(data)

print("[2/7] Rebalanceo Mensual...")
capital_mensual, rebal_mensual = rebalanceo_periodico(data, frecuencia_dias=30)

print("[3/7] Rebalanceo Trimestral...")
capital_trimestral, rebal_trimestral = rebalanceo_periodico(data, frecuencia_dias=90)

print("[4/7] Rebalanceo Anual...")
capital_anual, rebal_anual = rebalanceo_periodico(data, frecuencia_dias=365)

print("[5/7] Threshold 5%...")
capital_th5, rebal_th5 = rebalanceo_threshold(data, threshold=0.05)

print("[6/7] Threshold 10%...")
capital_th10, rebal_th10 = rebalanceo_threshold(data, threshold=0.10)

print("[7/7] Threshold 15%...")
capital_th15, rebal_th15 = rebalanceo_threshold(data, threshold=0.15)

# RESULTADOS
print("\n" + "="*80)
print("RESULTADOS COMPARATIVOS")
print("="*80 + "\n")

resultados = []

for nombre, capital_series, num_rebal in [
    ("Buy and Hold", capital_bh, rebal_bh),
    ("Rebalanceo Mensual", capital_mensual, rebal_mensual),
    ("Rebalanceo Trimestral", capital_trimestral, rebal_trimestral),
    ("Rebalanceo Anual", capital_anual, rebal_anual),
    ("Threshold 5%", capital_th5, rebal_th5),
    ("Threshold 10%", capital_th10, rebal_th10),
    ("Threshold 15%", capital_th15, rebal_th15)
]:
    capital_final = capital_series.iloc[-1]
    retorno = ((capital_final / 10000) - 1) * 100
    
    # Calcular Sharpe
    retornos_diarios = capital_series.pct_change().dropna()
    if len(retornos_diarios) > 0 and retornos_diarios.std() > 0:
        sharpe = (retornos_diarios.mean() * 252 - 0.04) / (retornos_diarios.std() * np.sqrt(252))
    else:
        sharpe = 0
    
    # Calcular Max Drawdown
    max_acum = capital_series.cummax()
    drawdown = (capital_series - max_acum) / max_acum
    max_dd = drawdown.min() * 100
    
    resultados.append({
        'Estrategia': nombre,
        'Capital Final': int(capital_final),
        'Retorno %': round(retorno, 2),
        'Sharpe': round(sharpe, 3),
        'Max DD %': round(max_dd, 2),
        'Rebalanceos': num_rebal
    })

df_resultados = pd.DataFrame(resultados)
print(df_resultados.to_string(index=False))

# ANÁLISIS
print("\n" + "="*80)
print("ANÁLISIS")
print("="*80)

mejor_retorno = df_resultados.loc[df_resultados['Retorno %'].idxmax()]
mejor_sharpe = df_resultados.loc[df_resultados['Sharpe'].idxmax()]
menos_rebalanceos = df_resultados.loc[df_resultados['Rebalanceos'].idxmin()]

print(f"\nMejor RETORNO: {mejor_retorno['Estrategia']}")
print(f"  Retorno: {mejor_retorno['Retorno %']:+.2f}%")
print(f"  Capital: ${mejor_retorno['Capital Final']:,}")
print(f"  Rebalanceos: {mejor_retorno['Rebalanceos']}")

print(f"\nMejor SHARPE (riesgo-retorno): {mejor_sharpe['Estrategia']}")
print(f"  Sharpe: {mejor_sharpe['Sharpe']:.3f}")
print(f"  Retorno: {mejor_sharpe['Retorno %']:+.2f}%")

print(f"\nMenos rebalanceos: {menos_rebalanceos['Estrategia']}")
print(f"  Rebalanceos: {menos_rebalanceos['Rebalanceos']}")
print(f"  Retorno: {menos_rebalanceos['Retorno %']:+.2f}%")

# CONCLUSIONES
print("\n" + "="*80)
print("CONCLUSIONES PROFESIONALES")
print("="*80)

print("\n1. TRADE-OFF: Retorno vs Costos")
print("   • Buy and Hold: Máximo retorno, pero más riesgo concentrado")
print("   • Rebalanceo frecuente: Más costos, menos retorno")
print("   • Threshold: Balance entre retorno y costos")

print("\n2. FRECUENCIA ÓPTIMA:")
print("   • Mensual: Demasiado frecuente (muchos costos)")
print("   • Trimestral/Anual: Balance razonable")
print("   • Threshold 10-15%: Óptimo para la mayoría")

print("\n3. RECOMENDACIÓN PROFESIONAL:")
print("   • Para portfolios pequeños (<$50k): Threshold 10-15%")
print("   • Para portfolios grandes (>$50k): Rebalanceo trimestral")
print("   • Para muy largo plazo (>10 años): Anual o threshold 15%")

print("\n4. COSTOS REALES:")
print("   • Cada rebalanceo cuesta: $10-50 en comisiones + spread")
costos_estimados = df_resultados.copy()
costos_estimados['Costos ($)'] = costos_estimados['Rebalanceos'] * 20
costos_estimados['Retorno Neto %'] = costos_estimados['Retorno %'] - (costos_estimados['Costos ($)'] / 10000 * 100)

print(f"\n   Ejemplo con $20 por rebalanceo:")
print(f"   - Mensual: {rebal_mensual} rebalanceos × $20 = ${rebal_mensual * 20} en costos")
print(f"   - Trimestral: {rebal_trimestral} rebalanceos × $20 = ${rebal_trimestral * 20} en costos")
print(f"   - Threshold 10%: {rebal_th10} rebalanceos × $20 = ${rebal_th10 * 20} en costos")

print("\n" + "="*80)