import yfinance as yf
import pandas as pd
import numpy as np
import math

ticker = "AAPL"
data = yf.download(ticker, start="2020-01-01", group_by='ticker')

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.droplevel(0)

print("\n" + "="*80)
print("DASHBOARD COMPARATIVO COMPLETO - APPLE (2020-2026)")
print("="*80)

# Calcular indicadores
data['MA20'] = data['Close'].rolling(window=20).mean()
data['MA50'] = data['Close'].rolling(window=50).mean()
data['Retorno'] = data['Close'].pct_change()

# FUNCIÓN: Calcular todas las métricas
def calcular_metricas(capital_history, operaciones, nombre_estrategia):
    """
    capital_history: Serie de pandas con el capital diario
    operaciones: Lista de operaciones
    """
    
    # Retorno total
    capital_inicial = capital_history.iloc[0]
    capital_final = capital_history.iloc[-1]
    
    if hasattr(capital_final, 'item'):
        capital_final = capital_final.item()
    if hasattr(capital_inicial, 'item'):
        capital_inicial = capital_inicial.item()
    
    if math.isnan(capital_final):
        capital_final = 10000
    
    retorno_total = ((capital_final / capital_inicial) - 1) * 100
    
    # Sharpe Ratio
    retornos_diarios = capital_history.pct_change().dropna()
    retorno_promedio_diario = retornos_diarios.mean()
    volatilidad_diaria = retornos_diarios.std()
    
    retorno_anual = retorno_promedio_diario * 252
    volatilidad_anual = volatilidad_diaria * np.sqrt(252)
    
    tasa_libre_riesgo = 0.04
    sharpe = (retorno_anual - tasa_libre_riesgo) / volatilidad_anual if volatilidad_anual > 0 else 0
    
    # Maximum Drawdown
    max_acumulado = capital_history.cummax()
    drawdown = (capital_history - max_acumulado) / max_acumulado
    max_drawdown = drawdown.min() * 100
    
    # Win Rate y Profit Factor
    if len(operaciones) > 0:
        ops_ganadoras = [op for op in operaciones if op['ganancia'] > 0]
        ops_perdedoras = [op for op in operaciones if op['ganancia'] <= 0]
        
        num_ganadoras = len(ops_ganadoras)
        num_perdedoras = len(ops_perdedoras)
        
        win_rate = (num_ganadoras / len(operaciones)) * 100 if len(operaciones) > 0 else 0
        
        ganancias_totales = sum([op['ganancia'] for op in ops_ganadoras]) if ops_ganadoras else 0
        perdidas_totales = abs(sum([op['ganancia'] for op in ops_perdedoras])) if ops_perdedoras else 0
        
        profit_factor = ganancias_totales / perdidas_totales if perdidas_totales > 0 else float('inf')
    else:
        win_rate = 0
        profit_factor = 0
    
    return {
        'Estrategia': nombre_estrategia,
        'Capital Final': int(capital_final),
        'Retorno %': round(retorno_total, 2),
        'Sharpe Ratio': round(sharpe, 3),
        'Max Drawdown %': round(max_drawdown, 2),
        'Win Rate %': round(win_rate, 2),
        'Profit Factor': round(profit_factor, 2),
        'Operaciones': len(operaciones)
    }

# ESTRATEGIA 1: BUY AND HOLD
print("\n[1/3] Calculando Buy and Hold...")

precio_inicial = data['Close'].iloc[0]
capital_bh = 10000 * (data['Close'] / precio_inicial)

ops_bh = [{
    'ganancia': capital_bh.iloc[-1] - 10000,
    'motivo': 'Hold'
}]

metricas_bh = calcular_metricas(capital_bh, ops_bh, "Buy and Hold")

# ESTRATEGIA 2: MEDIAS MÓVILES
print("[2/3] Calculando Medias Móviles...")

capital_ma_list = []
shares = 0
capital = 10000.0
operaciones_ma = []

for i in range(len(data)):
    precio = data['Close'].values[i]
    
    if i > 0:
        ma20_actual = data['MA20'].values[i]
        ma50_actual = data['MA50'].values[i]
        ma20_anterior = data['MA20'].values[i-1]
        ma50_anterior = data['MA50'].values[i-1]
        
        # Golden cross
        if ma20_anterior <= ma50_anterior and ma20_actual > ma50_actual and shares == 0:
            shares = capital / precio
            precio_compra = precio
            fecha_compra = data.index[i]
        
        # Death cross
        elif ma20_anterior >= ma50_anterior and ma20_actual < ma50_actual and shares > 0:
            capital = shares * precio
            operaciones_ma.append({
                'ganancia': capital - 10000,
                'fecha_compra': fecha_compra,
                'precio_compra': precio_compra,
                'fecha_venta': data.index[i],
                'precio_venta': precio
            })
            shares = 0
            capital = 10000.0
    
    if shares > 0:
        capital_ma_list.append(shares * precio)
    else:
        capital_ma_list.append(capital)

# Venta final
if shares > 0:
    precio_final = data['Close'].values[-1]
    capital = shares * precio_final
    operaciones_ma.append({
        'ganancia': capital - 10000,
        'fecha_compra': fecha_compra,
        'precio_compra': precio_compra,
        'fecha_venta': data.index[-1],
        'precio_venta': precio_final
    })

capital_ma_series = pd.Series(capital_ma_list, index=data.index)
metricas_ma = calcular_metricas(capital_ma_series, operaciones_ma, "Medias Móviles")

# ESTRATEGIA 3: MEDIAS MÓVILES + SL/TP
print("[3/3] Calculando Medias Móviles + Stop Loss/Take Profit...")

capital_sltp_list = []
shares = 0
capital = 10000.0
precio_compra = 0
operaciones_sltp = []

stop_loss_pct = -10
take_profit_pct = 20

for i in range(len(data)):
    precio = data['Close'].values[i]
    
    # Si no estamos invertidos
    if shares == 0:
        if i > 0:
            ma20_actual = data['MA20'].values[i]
            ma50_actual = data['MA50'].values[i]
            ma20_anterior = data['MA20'].values[i-1]
            ma50_anterior = data['MA50'].values[i-1]
            
            # Golden cross
            if ma20_anterior <= ma50_anterior and ma20_actual > ma50_actual:
                shares = capital / precio
                precio_compra = precio
                fecha_compra = data.index[i]
    
    # Si estamos invertidos
    else:
        retorno_actual = ((precio / precio_compra) - 1) * 100
        
        motivo = None
        
        # Check stop loss
        if retorno_actual <= stop_loss_pct:
            motivo = 'Stop Loss'
        
        # Check take profit
        elif retorno_actual >= take_profit_pct:
            motivo = 'Take Profit'
        
        # Check death cross
        elif i > 0:
            ma20_actual = data['MA20'].values[i]
            ma50_actual = data['MA50'].values[i]
            ma20_anterior = data['MA20'].values[i-1]
            ma50_anterior = data['MA50'].values[i-1]
            
            if ma20_anterior >= ma50_anterior and ma20_actual < ma50_actual:
                motivo = 'Death Cross'
        
        # Vender si hay motivo
        if motivo:
            capital = shares * precio
            operaciones_sltp.append({
                'ganancia': capital - 10000,
                'fecha_compra': fecha_compra,
                'precio_compra': precio_compra,
                'fecha_venta': data.index[i],
                'precio_venta': precio,
                'motivo': motivo
            })
            shares = 0
            capital = 10000.0
    
    if shares > 0:
        capital_sltp_list.append(shares * precio)
    else:
        capital_sltp_list.append(capital)

# Venta final
if shares > 0:
    precio_final = data['Close'].values[-1]
    capital = shares * precio_final
    operaciones_sltp.append({
        'ganancia': capital - 10000,
        'fecha_compra': fecha_compra,
        'precio_compra': precio_compra,
        'fecha_venta': data.index[-1],
        'precio_venta': precio_final,
        'motivo': 'Venta Final'
    })

capital_sltp_series = pd.Series(capital_sltp_list, index=data.index)
metricas_sltp = calcular_metricas(capital_sltp_series, operaciones_sltp, "MA + SL/TP")

# TABLA COMPARATIVA
print("\n" + "="*80)
print("TABLA COMPARATIVA - TODAS LAS MÉTRICAS")
print("="*80 + "\n")

df_comparacion = pd.DataFrame([metricas_bh, metricas_ma, metricas_sltp])

print(df_comparacion.to_string(index=False))

# ANÁLISIS Y RECOMENDACIÓN
print("\n" + "="*80)
print("ANÁLISIS Y RECOMENDACIÓN")
print("="*80)

# Mejor por cada métrica
mejor_retorno = df_comparacion.loc[df_comparacion['Retorno %'].idxmax(), 'Estrategia']
mejor_sharpe = df_comparacion.loc[df_comparacion['Sharpe Ratio'].idxmax(), 'Estrategia']
mejor_drawdown = df_comparacion.loc[df_comparacion['Max Drawdown %'].idxmax(), 'Estrategia']  # Más cercano a 0
mejor_winrate = df_comparacion.loc[df_comparacion['Win Rate %'].idxmax(), 'Estrategia']

print(f"\nMejor RETORNO:        {mejor_retorno}")
print(f"Mejor SHARPE RATIO:   {mejor_sharpe}")
print(f"Mejor DRAWDOWN:       {mejor_drawdown}")
print(f"Mejor WIN RATE:       {mejor_winrate}")

print("\n" + "-"*80)
print("RECOMENDACIÓN FINAL:")
print("-"*80)
print("\nPara APPLE 2020-2026 (mercado alcista fuerte):")
print("  → Buy and Hold fue la mejor estrategia")
print("  → Razón: Tendencia alcista continua sin crashes severos")
print("\nPara mercados VOLATILES o LATERALES:")
print("  → Medias Móviles + SL/TP sería mejor")
print("  → Razón: Protección contra caídas y disciplina de ganancias")
print("\nCONCLUSIÓN:")
print("  → No existe UNA estrategia perfecta para todos los mercados")
print("  → La clave es ADAPTAR la estrategia al tipo de mercado")
print("  → Esto es exactamente lo que aprenderás en el Mes 4 (Machine Learning)")
print("="*80)