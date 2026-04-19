import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

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
print("SCREENING ACTIVO - QUE ACCIONES COMPRAR HOY (18 MARZO 2026)?")
print("="*80)
print("\nAplicando 4 filtros para encontrar las mejores oportunidades...\n")

resultados = []

for i, ticker in enumerate(tickers_sp500, 1):
    try:
        print("[" + str(i) + "/" + str(len(tickers_sp500)) + "] Analizando " + ticker + "...", end=" ")
        
        # Descargar datos recientes (últimos 2 años + un poco más para MAs)
        data = yf.download(ticker, start="2024-01-01", end="2026-03-18", 
                          progress=False, group_by='ticker')
        
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(0)
        
        if len(data) < 100:
            print("Datos insuficientes")
            continue
        
        # FILTRO 1: Sharpe Ratio reciente (últimos 2 años)
        retornos = data['Close'].pct_change().dropna()
        retorno_anual = retornos.mean() * 252
        volatilidad_anual = retornos.std() * np.sqrt(252)
        sharpe = (retorno_anual - 0.04) / volatilidad_anual if volatilidad_anual > 0 else 0
        
        if sharpe < 0.5:
            print("FILTRADO - Sharpe bajo")
            continue
        
        # FILTRO 2: Señal técnica (Medias Móviles)
        data['MA20'] = data['Close'].rolling(window=20).mean()
        data['MA50'] = data['Close'].rolling(window=50).mean()
        
        ma20_actual = data['MA20'].iloc[-1]
        ma50_actual = data['MA50'].iloc[-1]
        
        if ma20_actual <= ma50_actual:
            print("FILTRADO - Tendencia bajista")
            continue
        
        # FILTRO 3: Momentum (últimos 3 meses)
        precio_3m_atras = data['Close'].iloc[-63] if len(data) >= 63 else data['Close'].iloc[0]
        precio_actual = data['Close'].iloc[-1]
        momentum_3m = ((precio_actual / precio_3m_atras) - 1) * 100
        
        if momentum_3m < 0:
            print("FILTRADO - Momentum negativo")
            continue
        
        # FILTRO 4: Drawdown último año
        data_1y = data.tail(252)
        max_acum = data_1y['Close'].cummax()
        drawdown = (data_1y['Close'] - max_acum) / max_acum
        max_dd = drawdown.min() * 100
        
        if max_dd < -40:
            print("FILTRADO - Drawdown alto")
            continue
        
        # Si llegó aquí, pasó todos los filtros
        # Calcular métricas adicionales
        retorno_2y = ((data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1) * 100
        
        resultados.append({
            'Ticker': ticker,
            'Precio Actual': round(precio_actual, 2),
            'Sharpe 2Y': round(sharpe, 3),
            'Momentum 3M %': round(momentum_3m, 2),
            'Max DD 1Y %': round(max_dd, 2),
            'Retorno 2Y %': round(retorno_2y, 2),
            'MA20': round(ma20_actual, 2),
            'MA50': round(ma50_actual, 2)
        })
        
        print("APROBADO")
        time.sleep(0.5)
        
    except Exception as e:
        print("Error")
        continue

# Crear DataFrame
df_filtrados = pd.DataFrame(resultados)

if len(df_filtrados) == 0:
    print("\n" + "="*80)
    print("NINGUN ACCION PASO TODOS LOS FILTROS")
    print("="*80)
    print("\nIntenta relajar los criterios o esperar mejores condiciones de mercado")
else:
    # Ordenar por Sharpe (mejor riesgo-retorno)
    df_filtrados = df_filtrados.sort_values('Sharpe 2Y', ascending=False)
    
    print("\n" + "="*80)
    print("ACCIONES QUE PASARON TODOS LOS FILTROS")
    print("="*80)
    print(str(len(df_filtrados)) + " acciones de " + str(len(tickers_sp500)) + " analizadas\n")
    
    print(df_filtrados.to_string(index=False))
    
    # Guardar a CSV
    df_filtrados.to_csv('acciones_compra_hoy.csv', index=False)
    
    # Análisis adicional
    print("\n" + "="*80)
    print("ANALISIS DE LAS CANDIDATAS")
    print("="*80)
    
    print("\nSharpe promedio: " + str(round(df_filtrados['Sharpe 2Y'].mean(), 3)))
    print("Momentum 3M promedio: " + str(round(df_filtrados['Momentum 3M %'].mean(), 2)) + "%")
    print("Max DD 1Y promedio: " + str(round(df_filtrados['Max DD 1Y %'].mean(), 2)) + "%")
    print("Retorno 2Y promedio: " + str(round(df_filtrados['Retorno 2Y %'].mean(), 2)) + "%")
    
    # Top 5 recomendaciones
    print("\n" + "="*80)
    print("TOP 5 RECOMENDACIONES DE COMPRA HOY")
    print("="*80)
    print("(Ordenadas por Sharpe - mejor riesgo-retorno)\n")
    
    top5 = df_filtrados.head(5)
    
    for idx, row in top5.iterrows():
        print("Ticker: " + row['Ticker'])
        print("  Precio actual: $" + str(row['Precio Actual']))
        print("  Sharpe 2Y: " + str(row['Sharpe 2Y']) + " (riesgo-retorno)")
        print("  Momentum 3M: +" + str(row['Momentum 3M %']) + "%")
        print("  Max Drawdown 1Y: " + str(row['Max DD 1Y %']) + "% (controlado)")
        print("  Retorno 2Y: +" + str(row['Retorno 2Y %']) + "%")
        print("")
    
    # Estrategia de inversión
    print("="*80)
    print("ESTRATEGIA DE INVERSION SUGERIDA")
    print("="*80)
    
    print("\nSi tienes $10,000 para invertir:")
    print("\nOpcion A - CONSERVADORA (Diversificacion maxima):")
    print("  Distribuir $" + str(10000 // len(df_filtrados)) + " en cada una de las " + str(len(df_filtrados)) + " acciones")
    
    if len(df_filtrados) >= 5:
        print("\nOpcion B - BALANCEADA (Top 5):")
        print("  Distribuir $2,000 en cada una de las top 5")
        print("  Acciones: " + ", ".join(top5['Ticker'].tolist()))
    
    if len(df_filtrados) >= 3:
        top3 = df_filtrados.head(3)
        print("\nOpcion C - AGRESIVA (Top 3):")
        print("  Distribuir $" + str(10000 // 3) + " en cada una de las top 3")
        print("  Acciones: " + ", ".join(top3['Ticker'].tolist()))
    
    print("\n" + "="*80)
    print("IMPORTANTE:")
    print("="*80)
    print("- Estas son oportunidades basadas en datos historicos")
    print("- El mercado puede cambiar en cualquier momento")
    print("- Siempre usa stop loss (-10%) para limitar perdidas")
    print("- Rebalancea cada 3-6 meses")
    print("- Esta NO es asesoria financiera, es analisis educativo")
    print("="*80)
    
    print("\nArchivo guardado: acciones_compra_hoy.csv")

print("\n" + "="*80)