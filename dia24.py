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
print("CORRELACIONES Y DIVERSIFICACION OPTIMA")
print("="*80)
print("\nDescargando datos de 50 acciones...")
print("Esto tomara 2-3 minutos...\n")

# Descargar retornos diarios de todas las acciones
retornos_dict = {}

for i, ticker in enumerate(tickers_sp500, 1):
    try:
        print("[" + str(i) + "/" + str(len(tickers_sp500)) + "] " + ticker + "...", end=" ")
        
        data = yf.download(ticker, start="2022-01-01", end="2026-03-20", 
                          progress=False, group_by='ticker')
        
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(0)
        
        if len(data) < 100:
            print("Datos insuficientes")
            continue
        
        # Calcular retornos diarios
        retornos = data['Close'].pct_change().dropna()
        retornos_dict[ticker] = retornos
        
        print("OK")
        time.sleep(0.5)
        
    except Exception as e:
        print("Error")
        continue

# Crear DataFrame de retornos
df_retornos = pd.DataFrame(retornos_dict)

print("\n" + "="*80)
print("MATRIZ DE CORRELACIONES")
print("="*80)

# Calcular matriz de correlaciones
matriz_correlacion = df_retornos.corr()

print("\nCorrelaciones calculadas para " + str(len(df_retornos.columns)) + " acciones")

# Encontrar pares con mayor y menor correlación
correlaciones_lista = []

for i in range(len(matriz_correlacion.columns)):
    for j in range(i+1, len(matriz_correlacion.columns)):
        ticker1 = matriz_correlacion.columns[i]
        ticker2 = matriz_correlacion.columns[j]
        corr = matriz_correlacion.iloc[i, j]
        correlaciones_lista.append({
            'Ticker 1': ticker1,
            'Ticker 2': ticker2,
            'Correlacion': round(corr, 3)
        })

df_correlaciones = pd.DataFrame(correlaciones_lista)
df_correlaciones = df_correlaciones.sort_values('Correlacion', ascending=False)

# Top 10 más correlacionadas
print("\n" + "="*80)
print("TOP 10 PARES MAS CORRELACIONADOS (se mueven JUNTAS)")
print("="*80)
print("Evita tener ambas en tu portfolio - no diversificas\n")

top_correlacionadas = df_correlaciones.head(10)
print(top_correlacionadas.to_string(index=False))

# Top 10 menos correlacionadas
print("\n" + "="*80)
print("TOP 10 PARES MENOS CORRELACIONADOS (se mueven INDEPENDIENTES)")
print("="*80)
print("Combinar estas acciones reduce riesgo sin reducir retorno\n")

menos_correlacionadas = df_correlaciones.tail(10).sort_values('Correlacion')
print(menos_correlacionadas.to_string(index=False))

# Correlación promedio por acción
print("\n" + "="*80)
print("CORRELACION PROMEDIO DE CADA ACCION")
print("="*80)
print("Acciones con baja correlacion promedio son mejores para diversificar\n")

corr_promedio = []
for ticker in matriz_correlacion.columns:
    # Correlación promedio con todas las demás (excluyendo consigo misma)
    corr_con_otras = matriz_correlacion[ticker].drop(ticker)
    promedio = corr_con_otras.mean()
    corr_promedio.append({
        'Ticker': ticker,
        'Corr Promedio': round(promedio, 3)
    })

df_corr_promedio = pd.DataFrame(corr_promedio)
df_corr_promedio = df_corr_promedio.sort_values('Corr Promedio')

print("TOP 10 ACCIONES MENOS CORRELACIONADAS (mejores para diversificar):")
print(df_corr_promedio.head(10).to_string(index=False))

# CONSTRUCCIÓN DE PORTFOLIO ÓPTIMO
print("\n" + "="*80)
print("CONSTRUCCION DE PORTFOLIO OPTIMO")
print("="*80)

# Seleccionar las 10 acciones menos correlacionadas entre sí
# Algoritmo greedy: empezar con la de menor correlación promedio, ir añadiendo las que menos correlación tengan con las ya seleccionadas

portfolio_optimo = []
acciones_disponibles = list(df_corr_promedio['Ticker'])

# Empezar con la de menor correlación promedio
primera = acciones_disponibles[0]
portfolio_optimo.append(primera)
acciones_disponibles.remove(primera)

# Añadir 9 más
while len(portfolio_optimo) < 10 and len(acciones_disponibles) > 0:
    mejor_candidata = None
    menor_corr = 999
    
    for candidata in acciones_disponibles:
        # Calcular correlación promedio con las ya en el portfolio
        corr_con_portfolio = []
        for accion_portfolio in portfolio_optimo:
            corr = matriz_correlacion.loc[candidata, accion_portfolio]
            corr_con_portfolio.append(corr)
        
        corr_promedio_candidata = np.mean(corr_con_portfolio)
        
        if corr_promedio_candidata < menor_corr:
            menor_corr = corr_promedio_candidata
            mejor_candidata = candidata
    
    if mejor_candidata:
        portfolio_optimo.append(mejor_candidata)
        acciones_disponibles.remove(mejor_candidata)

print("\nPORTFOLIO OPTIMO (10 acciones menos correlacionadas):")
for i, ticker in enumerate(portfolio_optimo, 1):
    corr_prom = df_corr_promedio[df_corr_promedio['Ticker'] == ticker]['Corr Promedio'].values[0]
    print(str(i) + ". " + ticker + " (Corr promedio: " + str(corr_prom) + ")")

# Calcular estadísticas del portfolio óptimo
print("\n" + "="*80)
print("ESTADISTICAS DEL PORTFOLIO OPTIMO")
print("="*80)

retornos_portfolio_optimo = df_retornos[portfolio_optimo]

# Retorno y volatilidad del portfolio (ponderado igualmente)
retornos_portfolio_diarios = retornos_portfolio_optimo.mean(axis=1)
retorno_anual_portfolio = retornos_portfolio_diarios.mean() * 252 * 100
volatilidad_anual_portfolio = retornos_portfolio_diarios.std() * np.sqrt(252) * 100

sharpe_portfolio = (retorno_anual_portfolio - 4) / volatilidad_anual_portfolio

print("\nRetorno anualizado: " + str(round(retorno_anual_portfolio, 2)) + "%")
print("Volatilidad anualizada: " + str(round(volatilidad_anual_portfolio, 2)) + "%")
print("Sharpe Ratio: " + str(round(sharpe_portfolio, 3)))

# Comparar con portfolio aleatorio de 10 acciones
print("\n" + "="*80)
print("COMPARACION: Portfolio Optimo vs Portfolio Aleatorio")
print("="*80)

# Tomar primeras 10 acciones (portfolio "malo" - no optimizado)
portfolio_aleatorio = tickers_sp500[:10]
retornos_portfolio_aleatorio = df_retornos[portfolio_aleatorio]
retornos_aleatorio_diarios = retornos_portfolio_aleatorio.mean(axis=1)
volatilidad_aleatorio = retornos_aleatorio_diarios.std() * np.sqrt(252) * 100

print("\nPortfolio OPTIMO (diversificado):")
print("  Volatilidad: " + str(round(volatilidad_anual_portfolio, 2)) + "%")
print("  Sharpe: " + str(round(sharpe_portfolio, 3)))

print("\nPortfolio ALEATORIO (primeras 10 tech):")
print("  Volatilidad: " + str(round(volatilidad_aleatorio, 2)) + "%")

reduccion_riesgo = ((volatilidad_aleatorio - volatilidad_anual_portfolio) / volatilidad_aleatorio) * 100
print("\nREDUCCION DE RIESGO: " + str(round(reduccion_riesgo, 2)) + "%")

# Guardar matriz de correlaciones
matriz_correlacion.to_csv('matriz_correlaciones.csv')
df_correlaciones.to_csv('pares_correlacionados.csv', index=False)

print("\n" + "="*80)
print("RECOMENDACION FINAL")
print("="*80)
print("\nSi tienes $10,000 para invertir:")
print("\nDistribuye $1,000 en cada una de estas 10 acciones:")
for ticker in portfolio_optimo:
    print("  - " + ticker)

print("\nBeneficios:")
print("  1. Baja correlacion entre acciones (diversificacion real)")
print("  2. Reduccion de riesgo del " + str(round(reduccion_riesgo, 2)) + "% vs portfolio no optimizado")
print("  3. Cuando una cae, otras suben (compensacion)")
print("  4. Sharpe Ratio " + str(round(sharpe_portfolio, 3)) + " (riesgo-retorno optimizado)")

print("\n" + "="*80)
print("Archivos guardados:")
print("  - matriz_correlaciones.csv")
print("  - pares_correlacionados.csv")
print("="*80)