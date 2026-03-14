import yfinance as yf
import pandas as pd
import math

ticker = "AAPL"
data = yf.download(ticker, start="2020-01-01", group_by='ticker')

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.droplevel(0)

print("\n" + "="*70)
print("STOP LOSS Y TAKE PROFIT - MEDIAS MOVILES")
print("="*70)

# Calcular medias móviles
data['MA20'] = data['Close'].rolling(window=20).mean()
data['MA50'] = data['Close'].rolling(window=50).mean()

# Función para simular con stop loss y take profit
def simular_con_sl_tp(data, stop_loss_pct, take_profit_pct):
    """
    stop_loss_pct: -10 significa stop loss al -10%
    take_profit_pct: 20 significa take profit al +20%
    """
    capital = 10000.0
    shares = 0.0
    precio_compra = 0.0
    operaciones = []
    
    for i in range(len(data)):
        precio_actual = data['Close'].values[i]
        fecha_actual = data.index[i]
        
        # Si NO estamos invertidos, buscar señal de compra
        if shares == 0.0:
            # Señal: MA20 > MA50 (golden cross o ya en tendencia alcista)
            if i > 0:
                ma20_actual = data['MA20'].values[i]
                ma50_actual = data['MA50'].values[i]
                ma20_anterior = data['MA20'].values[i-1]
                ma50_anterior = data['MA50'].values[i-1]
                
                # Golden cross: MA20 cruza por encima de MA50
                if ma20_anterior <= ma50_anterior and ma20_actual > ma50_actual:
                    shares = capital / precio_actual
                    precio_compra = precio_actual
                    fecha_compra = fecha_actual
        
        # Si estamos invertidos, verificar stop loss, take profit o señal de venta
        else:
            retorno_actual = ((precio_actual / precio_compra) - 1) * 100
            
            # Check stop loss
            if retorno_actual <= stop_loss_pct:
                capital = shares * precio_actual
                operaciones.append({
                    'fecha_compra': fecha_compra,
                    'precio_compra': precio_compra,
                    'fecha_venta': fecha_actual,
                    'precio_venta': precio_actual,
                    'ganancia': capital - 10000,
                    'motivo': 'Stop Loss'
                })
                shares = 0.0
                capital = 10000.0
            
            # Check take profit
            elif retorno_actual >= take_profit_pct:
                capital = shares * precio_actual
                operaciones.append({
                    'fecha_compra': fecha_compra,
                    'precio_compra': precio_compra,
                    'fecha_venta': fecha_actual,
                    'precio_venta': precio_actual,
                    'ganancia': capital - 10000,
                    'motivo': 'Take Profit'
                })
                shares = 0.0
                capital = 10000.0
            
            # Check death cross (señal de venta normal)
            elif i > 0:
                ma20_actual = data['MA20'].values[i]
                ma50_actual = data['MA50'].values[i]
                ma20_anterior = data['MA20'].values[i-1]
                ma50_anterior = data['MA50'].values[i-1]
                
                # Death cross: MA20 cruza por debajo de MA50
                if ma20_anterior >= ma50_anterior and ma20_actual < ma50_actual:
                    capital = shares * precio_actual
                    operaciones.append({
                        'fecha_compra': fecha_compra,
                        'precio_compra': precio_compra,
                        'fecha_venta': fecha_actual,
                        'precio_venta': precio_actual,
                        'ganancia': capital - 10000,
                        'motivo': 'Death Cross'
                    })
                    shares = 0.0
                    capital = 10000.0
    
    # Venta final si aún tienes acciones
    if shares > 0.0:
        precio_final = data['Close'].values[-1]
        capital = shares * precio_final
        operaciones.append({
            'fecha_compra': fecha_compra,
            'precio_compra': precio_compra,
            'fecha_venta': data.index[-1],
            'precio_venta': precio_final,
            'ganancia': capital - 10000,
            'motivo': 'Venta Final'
        })
    
    if hasattr(capital, 'item'):
        capital = capital.item()
    
    if math.isnan(capital):
        capital = 10000.0
    
    return capital, operaciones

# ESCENARIO 1: SIN stop loss ni take profit (baseline)
print("\n[1] BASELINE: Sin Stop Loss ni Take Profit")
print("-" * 70)

capital_base, ops_base = simular_con_sl_tp(data, stop_loss_pct=-999, take_profit_pct=999)
retorno_base = ((capital_base / 10000) - 1) * 100

print(f"Capital final: ${int(capital_base)}")
print(f"Retorno: +{round(retorno_base, 2)}%")
print(f"Operaciones totales: {len(ops_base)}")

# ESCENARIO 2: Stop Loss -10%
print("\n[2] CON Stop Loss -10% (sin take profit)")
print("-" * 70)

capital_sl, ops_sl = simular_con_sl_tp(data, stop_loss_pct=-10, take_profit_pct=999)
retorno_sl = ((capital_sl / 10000) - 1) * 100

print(f"Capital final: ${int(capital_sl)}")
print(f"Retorno: +{round(retorno_sl, 2)}%")
print(f"Operaciones totales: {len(ops_sl)}")

# Contar por motivo
sl_count = len([op for op in ops_sl if op['motivo'] == 'Stop Loss'])
print(f"Veces que se activó Stop Loss: {sl_count}")

# ESCENARIO 3: Take Profit +20%
print("\n[3] CON Take Profit +20% (sin stop loss)")
print("-" * 70)

capital_tp, ops_tp = simular_con_sl_tp(data, stop_loss_pct=-999, take_profit_pct=20)
retorno_tp = ((capital_tp / 10000) - 1) * 100

print(f"Capital final: ${int(capital_tp)}")
print(f"Retorno: +{round(retorno_tp, 2)}%")
print(f"Operaciones totales: {len(ops_tp)}")

tp_count = len([op for op in ops_tp if op['motivo'] == 'Take Profit'])
print(f"Veces que se activó Take Profit: {tp_count}")

# ESCENARIO 4: Ambos (Stop Loss -10% + Take Profit +20%)
print("\n[4] CON Stop Loss -10% Y Take Profit +20%")
print("-" * 70)

capital_both, ops_both = simular_con_sl_tp(data, stop_loss_pct=-10, take_profit_pct=20)
retorno_both = ((capital_both / 10000) - 1) * 100

print(f"Capital final: ${int(capital_both)}")
print(f"Retorno: +{round(retorno_both, 2)}%")
print(f"Operaciones totales: {len(ops_both)}")

sl_count_both = len([op for op in ops_both if op['motivo'] == 'Stop Loss'])
tp_count_both = len([op for op in ops_both if op['motivo'] == 'Take Profit'])
dc_count_both = len([op for op in ops_both if op['motivo'] == 'Death Cross'])

print(f"Stop Loss activados: {sl_count_both}")
print(f"Take Profit activados: {tp_count_both}")
print(f"Death Cross: {dc_count_both}")

# COMPARACIÓN FINAL
print("\n" + "="*70)
print("COMPARACIÓN FINAL")
print("="*70)

print(f"\n1. Sin SL/TP:           ${int(capital_base):,} (+{round(retorno_base, 2)}%)")
print(f"2. Solo SL -10%:        ${int(capital_sl):,} (+{round(retorno_sl, 2)}%)")
print(f"3. Solo TP +20%:        ${int(capital_tp):,} (+{round(retorno_tp, 2)}%)")
print(f"4. SL -10% + TP +20%:   ${int(capital_both):,} (+{round(retorno_both, 2)}%)")

# Determinar ganador
resultados = [
    ("Sin SL/TP", capital_base),
    ("Solo SL -10%", capital_sl),
    ("Solo TP +20%", capital_tp),
    ("SL + TP", capital_both)
]

ganador = max(resultados, key=lambda x: x[1])

print(f"\nMEJOR ESTRATEGIA: {ganador[0]}")
print("="*70)