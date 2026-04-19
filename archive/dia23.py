import yfinance as yf
import pandas as pd
import numpy as np
import time

tickers_sp500 = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
    "BRK-B", "JPM", "V", "MA", "BAC", "WFC", "GS",
    "JNJ", "UNH", "PFE", "ABBV", "TMO", "MRK", "LLY",
    "WMT", "HD", "PG", "KO", "PEP", "COST", "NKE",
    "BA", "CAT", "HON", "UPS", "GE", "MMM",
    "XOM", "CVX", "COP",
    "VZ", "T", "TMUS",
    "DIS", "NFLX", "INTC", "CSCO", "ADBE", "CRM", "ORCL", "AMD"
]

print("\n" + "="*80)
print("BACKTESTING MASIVO - ESTRATEGIA MA + SL/TP EN 50 ACCIONES")
print("="*80)
print("\nAplicando estrategia a todas las acciones del S&P 500...")
print("Esto tomara 2-3 minutos...\n")

def simular_estrategia(data, stop_loss_pct=-10, take_profit_pct=20):
    """Simular estrategia MA + SL/TP"""
    
    # Calcular MAs
    data['MA20'] = data['Close'].rolling(window=20).mean()
    data['MA50'] = data['Close'].rolling(window=50).mean()
    
    capital = 10000.0
    shares = 0.0
    precio_compra = 0.0
    operaciones = 0
    
    for i in range(len(data)):
        precio = data['Close'].values[i]
        
        # Si no estamos invertidos, buscar golden cross
        if shares == 0.0 and i > 0:
            ma20_actual = data['MA20'].values[i]
            ma50_actual = data['MA50'].values[i]
            ma20_anterior = data['MA20'].values[i-1]
            ma50_anterior = data['MA50'].values[i-1]
            
            if ma20_anterior <= ma50_anterior and ma20_actual > ma50_actual:
                shares = capital / precio
                precio_compra = precio
        
        # Si estamos invertidos, verificar SL/TP o death cross
        elif shares > 0.0:
            retorno = ((precio / precio_compra) - 1) * 100
            
            # Stop loss
            if retorno <= stop_loss_pct:
                capital = shares * precio
                shares = 0.0
                operaciones += 1
            
            # Take profit
            elif retorno >= take_profit_pct:
                capital = shares * precio
                shares = 0.0
                operaciones += 1
            
            # Death cross
            elif i > 0:
                ma20_actual = data['MA20'].values[i]
                ma50_actual = data['MA50'].values[i]
                ma20_anterior = data['MA20'].values[i-1]
                ma50_anterior = data['MA50'].values[i-1]
                
                if ma20_anterior >= ma50_anterior and ma20_actual < ma50_actual:
                    capital = shares * precio
                    shares = 0.0
                    operaciones += 1
    
    # Venta final
    if shares > 0.0:
        capital = shares * data['Close'].values[-1]
    
    return capital, operaciones

resultados = []

for i, ticker in enumerate(tickers_sp500, 1):
    try:
        print("[" + str(i) + "/" + str(len(tickers_sp500)) + "] " + ticker + "...", end=" ")
        
        # Descargar datos
        data = yf.download(ticker, start="2020-01-01", end="2026-03-19", 
                          progress=False, group_by='ticker')
        
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(0)
        
        if len(data) < 100:
            print("Datos insuficientes")
            continue
        
        # BUY AND HOLD
        precio_inicial = data['Close'].iloc[0]
        precio_final = data['Close'].iloc[-1]
        capital_bh = 10000 * (precio_final / precio_inicial)
        retorno_bh = ((capital_bh / 10000) - 1) * 100
        
        # ESTRATEGIA MA + SL/TP
        capital_estrategia, operaciones = simular_estrategia(data.copy())
        retorno_estrategia = ((capital_estrategia / 10000) - 1) * 100
        
        # Ventaja de la estrategia
        ventaja = retorno_estrategia - retorno_bh
        
        # Calcular volatilidad
        retornos = data['Close'].pct_change().dropna()
        volatilidad_anual = retornos.std() * np.sqrt(252) * 100
        
        resultados.append({
            'Ticker': ticker,
            'BH %': round(retorno_bh, 2),
            'Estrategia %': round(retorno_estrategia, 2),
            'Ventaja %': round(ventaja, 2),
            'Operaciones': operaciones,
            'Volatilidad %': round(volatilidad_anual, 2)
        })
        
        print("OK")
        time.sleep(0.5)
        
    except Exception as e:
        print("Error")
        continue

# Crear DataFrame
df_resultados = pd.DataFrame(resultados)

# Guardar
df_resultados.to_csv('backtesting_masivo_50.csv', index=False)

# ANÁLISIS
print("\n" + "="*80)
print("RESULTADOS COMPLETOS")
print("="*80 + "\n")

# Ordenar por ventaja
df_ordenado = df_resultados.sort_values('Ventaja %', ascending=False)
print(df_ordenado.to_string(index=False))

# ESTADÍSTICAS
print("\n" + "="*80)
print("ESTADISTICAS GENERALES")
print("="*80)

estrategia_gana = len(df_resultados[df_resultados['Ventaja %'] > 0])
bh_gana = len(df_resultados[df_resultados['Ventaja %'] <= 0])

print("\nAcciones donde ESTRATEGIA gana: " + str(estrategia_gana) + "/" + str(len(df_resultados)) + 
      " (" + str(round(estrategia_gana/len(df_resultados)*100, 1)) + "%)")
print("Acciones donde BUY AND HOLD gana: " + str(bh_gana) + "/" + str(len(df_resultados)) + 
      " (" + str(round(bh_gana/len(df_resultados)*100, 1)) + "%)")

ventaja_promedio = df_resultados['Ventaja %'].mean()
print("\nVentaja promedio de la estrategia: " + str(round(ventaja_promedio, 2)) + "%")

retorno_promedio_estrategia = df_resultados['Estrategia %'].mean()
retorno_promedio_bh = df_resultados['BH %'].mean()

print("\nRetorno promedio con estrategia: " + str(round(retorno_promedio_estrategia, 2)) + "%")
print("Retorno promedio con buy and hold: " + str(round(retorno_promedio_bh, 2)) + "%")

# TOP 10 donde la estrategia GANA más
print("\n" + "="*80)
print("TOP 10: Estrategia SUPERA a Buy and Hold")
print("="*80 + "\n")

top_estrategia = df_ordenado.head(10)
print(top_estrategia.to_string(index=False))

# TOP 10 donde Buy and Hold GANA más
print("\n" + "="*80)
print("TOP 10: Buy and Hold SUPERA a Estrategia")
print("="*80 + "\n")

top_bh = df_ordenado.tail(10)
print(top_bh.to_string(index=False))

# ANÁLISIS POR VOLATILIDAD
print("\n" + "="*80)
print("ANALISIS: Estrategia vs Volatilidad")
print("="*80)

# Dividir por volatilidad
baja_vol = df_resultados[df_resultados['Volatilidad %'] < 30]
alta_vol = df_resultados[df_resultados['Volatilidad %'] >= 30]

if len(baja_vol) > 0:
    ventaja_baja_vol = baja_vol['Ventaja %'].mean()
    print("\nAcciones baja volatilidad (< 30%):")
    print("  Cantidad: " + str(len(baja_vol)))
    print("  Ventaja promedio estrategia: " + str(round(ventaja_baja_vol, 2)) + "%")

if len(alta_vol) > 0:
    ventaja_alta_vol = alta_vol['Ventaja %'].mean()
    print("\nAcciones alta volatilidad (>= 30%):")
    print("  Cantidad: " + str(len(alta_vol)))
    print("  Ventaja promedio estrategia: " + str(round(ventaja_alta_vol, 2)) + "%")

# CONCLUSIONES
print("\n" + "="*80)
print("CONCLUSIONES")
print("="*80)

if ventaja_promedio > 5:
    print("\nLa estrategia MA + SL/TP SUPERA a Buy and Hold en promedio")
    print("Recomendacion: Usar la estrategia activa")
elif ventaja_promedio > -5:
    print("\nLa estrategia MA + SL/TP es SIMILAR a Buy and Hold")
    print("Recomendacion: Depende del perfil de riesgo")
else:
    print("\nBuy and Hold SUPERA a la estrategia MA + SL/TP en promedio")
    print("Recomendacion: Usar buy and hold en mercados alcistas fuertes")

if len(baja_vol) > 0 and len(alta_vol) > 0:
    if ventaja_baja_vol > ventaja_alta_vol:
        print("\nLa estrategia funciona MEJOR en acciones de baja volatilidad")
    else:
        print("\nLa estrategia funciona MEJOR en acciones de alta volatilidad")

print("\n" + "="*80)
print("Archivo guardado: backtesting_masivo_50.csv")
print("="*80)