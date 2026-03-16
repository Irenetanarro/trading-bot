import yfinance as yf
import pandas as pd
import numpy as np
import time

# 50 acciones del S&P 500
tickers_sp500 = [
    # Tech Giants
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
    
    # Finance
    "BRK-B", "JPM", "V", "MA", "BAC", "WFC", "GS",
    
    # Healthcare
    "JNJ", "UNH", "PFE", "ABBV", "TMO", "MRK", "LLY",
    
    # Consumer
    "WMT", "HD", "PG", "KO", "PEP", "COST", "NKE",
    
    # Industrial
    "BA", "CAT", "HON", "UPS", "GE", "MMM",
    
    # Energy
    "XOM", "CVX", "COP",
    
    # Telecom
    "VZ", "T", "TMUS",
    
    # Other
    "DIS", "NFLX", "INTC", "CSCO", "ADBE", "CRM", "ORCL", "AMD"
]

print("\n" + "="*80)
print(f"ANÁLISIS MASIVO - {len(tickers_sp500)} ACCIONES DEL S&P 500")
print("="*80)
print(f"\nDescargando datos históricos (2020-2026)...")
print("Esto puede tomar 1-2 minutos...\n")

resultados = []

for i, ticker in enumerate(tickers_sp500, 1):
    try:
        print(f"[{i}/{len(tickers_sp500)}] Procesando {ticker}...", end=" ")
        
        # Descargar datos
        data = yf.download(ticker, start="2020-01-01", end="2026-03-16", 
                          progress=False, group_by='ticker')
        
        # Manejar multi-index si existe
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(0)
        
        # Verificar que hay datos
        if len(data) < 100:
            print("❌ Datos insuficientes")
            continue
        
        # MÉTRICAS BÁSICAS
        precio_inicial = data['Close'].iloc[0]
        precio_final = data['Close'].iloc[-1]
        precio_actual = precio_final
        
        # Retorno total
        retorno_total = ((precio_final / precio_inicial) - 1) * 100
        
        # Sharpe Ratio
        retornos_diarios = data['Close'].pct_change().dropna()
        retorno_promedio_diario = retornos_diarios.mean()
        volatilidad_diaria = retornos_diarios.std()
        
        retorno_anual = retorno_promedio_diario * 252
        volatilidad_anual = volatilidad_diaria * np.sqrt(252)
        
        sharpe = (retorno_anual - 0.04) / volatilidad_anual if volatilidad_anual > 0 else 0
        
        # Maximum Drawdown
        max_acumulado = data['Close'].cummax()
        drawdown = (data['Close'] - max_acumulado) / max_acumulado
        max_drawdown = drawdown.min() * 100
        
        # Volatilidad anualizada
        volatilidad_pct = volatilidad_anual * 100
        
        # Medias móviles (señal actual)
        data['MA20'] = data['Close'].rolling(window=20).mean()
        data['MA50'] = data['Close'].rolling(window=50).mean()
        
        ma20_actual = data['MA20'].iloc[-1]
        ma50_actual = data['MA50'].iloc[-1]
        
        if ma20_actual > ma50_actual:
            senal_actual = "ALCISTA"
        else:
            senal_actual = "BAJISTA"
        
        # Guardar resultados
        resultados.append({
            'Ticker': ticker,
            'Precio Actual': round(precio_actual, 2),
            'Retorno %': round(retorno_total, 2),
            'Sharpe Ratio': round(sharpe, 3),
            'Max Drawdown %': round(max_drawdown, 2),
            'Volatilidad %': round(volatilidad_pct, 2),
            'Señal MA': senal_actual
        })
        
        print("✅")
        
        # Pausa para no sobrecargar la API de Yahoo Finance
        time.sleep(0.5)
        
    except Exception as e:
        print(f"❌ Error: {str(e)[:50]}")
        continue

# Crear DataFrame
df_resultados = pd.DataFrame(resultados)

# Ordenar por Sharpe Ratio (mejor métrica de riesgo-retorno)
df_resultados = df_resultados.sort_values('Sharpe Ratio', ascending=False)

print("\n" + "="*80)
print("RESULTADOS COMPLETOS")
print("="*80 + "\n")

print(df_resultados.to_string(index=False))

# Guardar a CSV
df_resultados.to_csv('sp500_analysis.csv', index=False)

print("\n" + "="*80)
print("TOP 10 ACCIONES POR SHARPE RATIO (Mejor riesgo-retorno)")
print("="*80 + "\n")

print(df_resultados.head(10).to_string(index=False))

print("\n" + "="*80)
print("BOTTOM 10 ACCIONES (Peor desempeño)")
print("="*80 + "\n")

print(df_resultados.tail(10).to_string(index=False))

print("\n" + "="*80)
print("ESTADÍSTICAS GENERALES DEL S&P 500")
print("="*80)

print(f"\nRetorno promedio:        {df_resultados['Retorno %'].mean():.2f}%")
print(f"Retorno mediano:         {df_resultados['Retorno %'].median():.2f}%")
print(f"Mejor retorno:           {df_resultados['Retorno %'].max():.2f}% ({df_resultados.loc[df_resultados['Retorno %'].idxmax(), 'Ticker']})")
print(f"Peor retorno:            {df_resultados['Retorno %'].min():.2f}% ({df_resultados.loc[df_resultados['Retorno %'].idxmin(), 'Ticker']})")

print(f"\nSharpe promedio:         {df_resultados['Sharpe Ratio'].mean():.3f}")
print(f"Mejor Sharpe:            {df_resultados['Sharpe Ratio'].max():.3f} ({df_resultados.loc[df_resultados['Sharpe Ratio'].idxmax(), 'Ticker']})")

print(f"\nDrawdown promedio:       {df_resultados['Max Drawdown %'].mean():.2f}%")
print(f"Peor Drawdown:           {df_resultados['Max Drawdown %'].min():.2f}% ({df_resultados.loc[df_resultados['Max Drawdown %'].idxmin(), 'Ticker']})")

print(f"\nVolatilidad promedio:    {df_resultados['Volatilidad %'].mean():.2f}%")

# Señales actuales
alcistas = len(df_resultados[df_resultados['Señal MA'] == 'ALCISTA'])
bajistas = len(df_resultados[df_resultados['Señal MA'] == 'BAJISTA'])

print(f"\nSeñales actuales:")
print(f"  Alcistas (MA20 > MA50): {alcistas} ({alcistas/len(df_resultados)*100:.1f}%)")
print(f"  Bajistas (MA20 < MA50): {bajistas} ({bajistas/len(df_resultados)*100:.1f}%)")

print("\n" + "="*80)
print(f"Archivo guardado: sp500_analysis.csv")
print("="*80)