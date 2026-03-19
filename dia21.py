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
print("ANALISIS HISTORICO: Podrias haber predicho los ganadores?")
print("="*80)
print("\nEscenario: Estas en enero 2020")
print("Solo tienes datos de 2015-2019")
print("Debes elegir las mejores acciones para 2020-2026\n")

# FASE 1: Analizar período histórico (2015-2019)
print("="*80)
print("FASE 1: Analizando desempeno historico (2015-2019)")
print("="*80)

resultados_historicos = []

for i, ticker in enumerate(tickers_sp500, 1):
    try:
        print("[" + str(i) + "/" + str(len(tickers_sp500)) + "] Analizando " + ticker + " (2015-2019)...", end=" ")
        
        # Descargar datos SOLO hasta 2019
        data_hist = yf.download(ticker, start="2015-01-01", end="2019-12-31", 
                               progress=False, group_by='ticker')
        
        if isinstance(data_hist.columns, pd.MultiIndex):
            data_hist.columns = data_hist.columns.droplevel(0)
        
        if len(data_hist) < 100:
            print("Datos insuficientes")
            continue
        
        # Calcular métricas históricas
        precio_inicial = data_hist['Close'].iloc[0]
        precio_final = data_hist['Close'].iloc[-1]
        
        retorno_historico = ((precio_final / precio_inicial) - 1) * 100
        
        # Sharpe histórico
        retornos = data_hist['Close'].pct_change().dropna()
        retorno_anual = retornos.mean() * 252
        volatilidad_anual = retornos.std() * np.sqrt(252)
        sharpe_historico = (retorno_anual - 0.04) / volatilidad_anual if volatilidad_anual > 0 else 0
        
        # Drawdown histórico
        max_acum = data_hist['Close'].cummax()
        drawdown = (data_hist['Close'] - max_acum) / max_acum
        max_dd_hist = drawdown.min() * 100
        
        resultados_historicos.append({
            'Ticker': ticker,
            'Retorno Hist %': round(retorno_historico, 2),
            'Sharpe Hist': round(sharpe_historico, 3),
            'Max DD Hist %': round(max_dd_hist, 2)
        })
        
        print("OK")
        time.sleep(0.5)
        
    except Exception as e:
        print("Error")
        continue

df_historico = pd.DataFrame(resultados_historicos)
df_historico = df_historico.sort_values('Sharpe Hist', ascending=False)

print("\n" + "="*80)
print("TOP 10 ACCIONES POR SHARPE HISTORICO (2015-2019)")
print("="*80)
print("Estas son las que hubieras elegido en enero 2020\n")

top_10_historico = df_historico.head(10)
print(top_10_historico.to_string(index=False))

# FASE 2: Ver qué pasó con esas acciones en 2020-2026
print("\n" + "="*80)
print("FASE 2: Como les fue a esas top 10 en 2020-2026?")
print("="*80)

tickers_top10 = top_10_historico['Ticker'].tolist()
resultados_futuro = []

for i, ticker in enumerate(tickers_top10, 1):
    try:
        print("[" + str(i) + "/10] Validando " + ticker + " (2020-2026)...", end=" ")
        
        # Descargar datos 2020-2026
        data_futuro = yf.download(ticker, start="2020-01-01", end="2026-03-17", 
                                 progress=False, group_by='ticker')
        
        if isinstance(data_futuro.columns, pd.MultiIndex):
            data_futuro.columns = data_futuro.columns.droplevel(0)
        
        precio_inicial = data_futuro['Close'].iloc[0]
        precio_final = data_futuro['Close'].iloc[-1]
        
        retorno_futuro = ((precio_final / precio_inicial) - 1) * 100
        
        # Sharpe futuro
        retornos = data_futuro['Close'].pct_change().dropna()
        retorno_anual = retornos.mean() * 252
        volatilidad_anual = retornos.std() * np.sqrt(252)
        sharpe_futuro = (retorno_anual - 0.04) / volatilidad_anual if volatilidad_anual > 0 else 0
        
        # Recuperar Sharpe histórico
        sharpe_hist = top_10_historico[top_10_historico['Ticker'] == ticker]['Sharpe Hist'].values[0]
        
        resultados_futuro.append({
            'Ticker': ticker,
            'Sharpe Hist': round(sharpe_hist, 3),
            'Sharpe Real': round(sharpe_futuro, 3),
            'Retorno %': round(retorno_futuro, 2),
            'Degradacion': round(sharpe_hist - sharpe_futuro, 3)
        })
        
        print("OK")
        time.sleep(0.5)
        
    except Exception as e:
        print("Error")
        continue

df_validacion = pd.DataFrame(resultados_futuro)

print("\n" + "="*80)
print("RESULTADOS: Sharpe Historico vs Sharpe Real")
print("="*80 + "\n")

print(df_validacion.to_string(index=False))

# ANÁLISIS
print("\n" + "="*80)
print("ANALISIS: Las ganadoras historicas siguieron ganando?")
print("="*80)

degradacion_promedio = df_validacion['Degradacion'].mean()
retorno_promedio_top10 = df_validacion['Retorno %'].mean()

mejores_siguieron = len(df_validacion[df_validacion['Sharpe Real'] > 0.5])
empeoraron = len(df_validacion[df_validacion['Degradacion'] > 0.3])

print("\nRetorno promedio del top 10: " + str(round(retorno_promedio_top10, 2)) + "%")
print("Degradacion promedio de Sharpe: " + str(round(degradacion_promedio, 3)))
print("\nAcciones que mantuvieron Sharpe > 0.5: " + str(mejores_siguieron) + "/10")
print("Acciones que degradaron significativamente: " + str(empeoraron) + "/10")

# NVDA
if 'NVDA' in tickers_top10:
    print("\nNVDA estaba en el top 10 historico: SI")
else:
    nvda_posicion = list(df_historico['Ticker']).index('NVDA') + 1 if 'NVDA' in list(df_historico['Ticker']) else 99
    print("\nNVDA estaba en el top 10 historico: NO")
    print("Posicion de NVDA en ranking historico: #" + str(nvda_posicion))

# CONCLUSIÓN
print("\n" + "="*80)
print("CONCLUSION")
print("="*80)

if degradacion_promedio < 0.2:
    print("\nLas ganadoras historicas MANTUVIERON su desempeno")
elif degradacion_promedio < 0.4:
    print("\nLas ganadoras historicas tuvieron degradacion MODERADA")
else:
    print("\nLas ganadoras historicas DEGRADARON significativamente")

print("\nSi hubieras invertido $10,000 en estas 10 acciones en 2020:")
print("Retorno promedio: +" + str(round(retorno_promedio_top10, 2)) + "%")
capital_final = 10000 * (1 + retorno_promedio_top10/100)
print("Capital final estimado: $" + str(int(capital_final)))

print("\n" + "="*80)