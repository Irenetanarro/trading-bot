import yfinance as yf
import pandas as pd

ticker = "AAPL"
data = yf.download(ticker, start="2020-01-01", group_by='ticker')

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.droplevel(0)

print("\n" + "="*70)
print("WIN RATE Y PROFIT FACTOR - APPLE (2020-2026)")
print("="*70)

# ESTRATEGIA: MEDIAS MOVILES
print("\n[1] MEDIAS MOVILES (Golden/Death Cross)")
print("-" * 70)

data['MA20'] = data['Close'].rolling(window=20).mean()
data['MA50'] = data['Close'].rolling(window=50).mean()
data['Signal_MA'] = 0
data.loc[data['MA20'] > data['MA50'], 'Signal_MA'] = 1
data['Position_MA'] = data['Signal_MA'].diff()

# Simular operaciones
capital = 10000.0
shares = 0.0
operaciones = []

for i in range(len(data)):
    pos = data['Position_MA'].values[i]
    precio = data['Close'].values[i]
    fecha = data.index[i]
    
    if pos == 1.0 and shares == 0.0:
        # COMPRA
        shares = capital / precio
        precio_compra = precio
        fecha_compra = fecha
        
    elif pos == -1.0 and shares > 0.0:
        # VENTA
        capital = shares * precio
        precio_venta = precio
        ganancia = capital - 10000
        
        # Registrar operación
        operaciones.append({
            'fecha_compra': fecha_compra,
            'precio_compra': precio_compra,
            'fecha_venta': fecha,
            'precio_venta': precio_venta,
            'ganancia': ganancia,
            'porcentaje': ((precio_venta / precio_compra) - 1) * 100
        })
        
        # Reiniciar para próxima operación
        capital = 10000.0
        shares = 0.0

print("Total de operaciones completas:", len(operaciones))

# Analizar operaciones
operaciones_ganadoras = [op for op in operaciones if op['ganancia'] > 0]
operaciones_perdedoras = [op for op in operaciones if op['ganancia'] <= 0]

num_ganadoras = len(operaciones_ganadoras)
num_perdedoras = len(operaciones_perdedoras)

win_rate = (num_ganadoras / len(operaciones)) * 100 if len(operaciones) > 0 else 0

print("\nOperaciones ganadoras:", num_ganadoras)
print("Operaciones perdedoras:", num_perdedoras)
print("Win Rate:", round(win_rate, 2), "%")

# Calcular ganancias y pérdidas totales
ganancias_totales = sum([op['ganancia'] for op in operaciones_ganadoras])
perdidas_totales = abs(sum([op['ganancia'] for op in operaciones_perdedoras]))

profit_factor = ganancias_totales / perdidas_totales if perdidas_totales > 0 else float('inf')

print("\nGanancias totales: $", round(ganancias_totales, 2))
print("Perdidas totales: $", round(perdidas_totales, 2))
print("Profit Factor:", round(profit_factor, 3))

# Promedio de ganancias y pérdidas
if num_ganadoras > 0:
    avg_win = ganancias_totales / num_ganadoras
    print("\nGanancia promedio por operacion ganadora: $", round(avg_win, 2))

if num_perdedoras > 0:
    avg_loss = perdidas_totales / num_perdedoras
    print("Perdida promedio por operacion perdedora: $", round(avg_loss, 2))

if num_ganadoras > 0 and num_perdedoras > 0:
    ratio_win_loss = avg_win / avg_loss
    print("Ratio Ganancia/Perdida:", round(ratio_win_loss, 2), "x")

# Mostrar las 5 mejores y 5 peores operaciones
print("\n" + "="*70)
print("TOP 5 MEJORES OPERACIONES")
print("="*70)

operaciones_ordenadas = sorted(operaciones, key=lambda x: x['ganancia'], reverse=True)

for i in range(min(5, len(operaciones_ordenadas))):
    op = operaciones_ordenadas[i]
    print(f"{i+1}. Compra: {str(op['fecha_compra'])[:10]} ${round(op['precio_compra'], 2)} → "
          f"Venta: {str(op['fecha_venta'])[:10]} ${round(op['precio_venta'], 2)} → "
          f"Ganancia: ${round(op['ganancia'], 2)} ({round(op['porcentaje'], 2)}%)")

print("\n" + "="*70)
print("TOP 5 PEORES OPERACIONES")
print("="*70)

operaciones_peores = sorted(operaciones, key=lambda x: x['ganancia'])

for i in range(min(5, len(operaciones_peores))):
    op = operaciones_peores[i]
    print(f"{i+1}. Compra: {str(op['fecha_compra'])[:10]} ${round(op['precio_compra'], 2)} → "
          f"Venta: {str(op['fecha_venta'])[:10]} ${round(op['precio_venta'], 2)} → "
          f"Perdida: ${round(op['ganancia'], 2)} ({round(op['porcentaje'], 2)}%)")

# Calificación
print("\n" + "="*70)
print("CALIFICACION")
print("="*70)

if win_rate < 50:
    cal_wr = "BAJO"
elif win_rate < 60:
    cal_wr = "DECENTE"
elif win_rate < 70:
    cal_wr = "BUENO"
else:
    cal_wr = "EXCELENTE"

print(f"Win Rate {round(win_rate, 1)}%: {cal_wr}")

if profit_factor < 1.0:
    cal_pf = "MALO - Pierdes dinero"
elif profit_factor < 1.5:
    cal_pf = "APENAS RENTABLE"
elif profit_factor < 2.0:
    cal_pf = "BUENO"
elif profit_factor < 3.0:
    cal_pf = "EXCELENTE"
else:
    cal_pf = "EXTRAORDINARIO"

print(f"Profit Factor {round(profit_factor, 2)}: {cal_pf}")

print("\nREFERENCIA:")
print("Win Rate bueno: > 55%")
print("Profit Factor bueno: > 1.5")
print("="*70)