import yfinance as yf
import pandas as pd
import numpy as np

# Descargar datos de 3 acciones con diferentes volatilidades
print("\n" + "="*80)
print("RISK PARITY - AAPL + MSFT + TSLA")
print("="*80)
print("\nDescargando datos...\n")

tickers = ["AAPL", "MSFT", "TSLA"]
data = yf.download(tickers, start="2020-01-01", end="2026-04-02", progress=False)['Close']

# Calcular retornos diarios
returns = data.pct_change().dropna()

# Calcular volatilidad anualizada de cada acción
print("="*80)
print("VOLATILIDAD DE CADA ACCIÓN")
print("="*80 + "\n")

volatilidades = {}
for ticker in tickers:
    vol_diaria = returns[ticker].std()
    vol_anual = vol_diaria * np.sqrt(252)
    volatilidades[ticker] = vol_anual
    print(f"{ticker}: {vol_anual*100:.2f}% anual")

# ESTRATEGIA 1: PORTFOLIO TRADICIONAL (Equal Weight = 33.33% cada uno)
print("\n" + "="*80)
print("ESTRATEGIA 1: EQUAL WEIGHT (33.33% cada acción)")
print("="*80)

def backtest_equal_weight(data, capital_inicial=10000):
    # 33.33% en cada acción
    shares = {}
    for ticker in tickers:
        shares[ticker] = (capital_inicial / 3) / data[ticker].iloc[0]
    
    capital_series = []
    for i in range(len(data)):
        valor_total = sum(shares[ticker] * data[ticker].iloc[i] for ticker in tickers)
        capital_series.append(valor_total)
    
    return pd.Series(capital_series, index=data.index)

capital_equal = backtest_equal_weight(data)

retorno_equal = ((capital_equal.iloc[-1] / 10000) - 1) * 100
retornos_equal = capital_equal.pct_change().dropna()
sharpe_equal = (retornos_equal.mean() * 252 - 0.04) / (retornos_equal.std() * np.sqrt(252))
max_acum = capital_equal.cummax()
drawdown = (capital_equal - max_acum) / max_acum
max_dd_equal = drawdown.min() * 100

print(f"\nCapital final: ${int(capital_equal.iloc[-1]):,}")
print(f"Retorno: {retorno_equal:+.2f}%")
print(f"Sharpe: {sharpe_equal:.3f}")
print(f"Max Drawdown: {max_dd_equal:.2f}%")

# Calcular contribución al riesgo en equal weight
print("\nContribución al RIESGO (Equal Weight):")
total_risk_ew = sum((1/3) * volatilidades[t] for t in tickers)
for ticker in tickers:
    peso = 1/3
    vol = volatilidades[ticker]
    contribucion_riesgo = (peso * vol) / total_risk_ew
    print(f"  {ticker}: {contribucion_riesgo*100:.1f}% del riesgo total")

# ESTRATEGIA 2: RISK PARITY
print("\n" + "="*80)
print("ESTRATEGIA 2: RISK PARITY (pesos por volatilidad inversa)")
print("="*80)

# Calcular pesos de Risk Parity
pesos_rp = {}
suma_inv_vol = sum(1/volatilidades[ticker] for ticker in tickers)

print("\nCálculo de pesos:")
for ticker in tickers:
    peso = (1/volatilidades[ticker]) / suma_inv_vol
    pesos_rp[ticker] = peso
    print(f"{ticker}: {peso*100:.2f}% (volatilidad: {volatilidades[ticker]*100:.2f}%)")

def backtest_risk_parity(data, pesos, capital_inicial=10000):
    shares = {}
    for ticker in tickers:
        shares[ticker] = (capital_inicial * pesos[ticker]) / data[ticker].iloc[0]
    
    capital_series = []
    for i in range(len(data)):
        valor_total = sum(shares[ticker] * data[ticker].iloc[i] for ticker in tickers)
        capital_series.append(valor_total)
    
    return pd.Series(capital_series, index=data.index)

capital_rp = backtest_risk_parity(data, pesos_rp)

retorno_rp = ((capital_rp.iloc[-1] / 10000) - 1) * 100
retornos_rp = capital_rp.pct_change().dropna()
sharpe_rp = (retornos_rp.mean() * 252 - 0.04) / (retornos_rp.std() * np.sqrt(252))
max_acum_rp = capital_rp.cummax()
drawdown_rp = (capital_rp - max_acum_rp) / max_acum_rp
max_dd_rp = drawdown_rp.min() * 100

print(f"\nCapital final: ${int(capital_rp.iloc[-1]):,}")
print(f"Retorno: {retorno_rp:+.2f}%")
print(f"Sharpe: {sharpe_rp:.3f}")
print(f"Max Drawdown: {max_dd_rp:.2f}%")

# Verificar que contribución al riesgo es igual
print("\nContribución al RIESGO (Risk Parity):")
total_risk_rp = sum(pesos_rp[t] * volatilidades[t] for t in tickers)
for ticker in tickers:
    peso = pesos_rp[ticker]
    vol = volatilidades[ticker]
    contribucion_riesgo = (peso * vol) / total_risk_rp
    print(f"  {ticker}: {contribucion_riesgo*100:.1f}% del riesgo total")

# COMPARACIÓN - ORDEN CORRECTO
print("\n" + "="*80)
print("COMPARACIÓN FINAL")
print("="*80 + "\n")

# Crear DataFrame en el orden correcto
resultados = pd.DataFrame([
    {
        'Estrategia': 'Equal Weight (33/33/33)',
        'Capital Final': int(capital_equal.iloc[-1]),
        'Retorno %': round(retorno_equal, 2),
        'Sharpe': round(sharpe_equal, 3),
        'Max DD %': round(max_dd_equal, 2)
    },
    {
        'Estrategia': 'Risk Parity',
        'Capital Final': int(capital_rp.iloc[-1]),
        'Retorno %': round(retorno_rp, 2),
        'Sharpe': round(sharpe_rp, 3),
        'Max DD %': round(max_dd_rp, 2)
    }
])

print(resultados.to_string(index=False))

# ANÁLISIS
print("\n" + "="*80)
print("ANÁLISIS")
print("="*80)

mejor_retorno = resultados.loc[resultados['Retorno %'].idxmax()]
mejor_sharpe = resultados.loc[resultados['Sharpe'].idxmax()]
mejor_dd = resultados.loc[resultados['Max DD %'].idxmax()]  # Más cercano a 0

print(f"\nMejor RETORNO: {mejor_retorno['Estrategia']}")
print(f"  Retorno: {mejor_retorno['Retorno %']:+.2f}%")

print(f"\nMejor SHARPE (riesgo-retorno): {mejor_sharpe['Estrategia']}")
print(f"  Sharpe: {mejor_sharpe['Sharpe']:.3f}")

print(f"\nMenor DRAWDOWN (menor caída): {mejor_dd['Estrategia']}")
print(f"  Max DD: {mejor_dd['Max DD %']:.2f}%")

# Diferencias clave
diff_retorno = retorno_equal - retorno_rp
diff_sharpe = sharpe_equal - sharpe_rp
diff_dd = abs(max_dd_equal) - abs(max_dd_rp)

print("\n" + "="*80)
print("DIFERENCIAS CLAVE")
print("="*80)

print(f"\nEqual Weight vs Risk Parity:")
print(f"  Retorno: Equal Weight gana por {diff_retorno:+.2f}%")
print(f"  Sharpe: Equal Weight {'gana' if diff_sharpe > 0 else 'pierde'} por {abs(diff_sharpe):.3f}")
print(f"  Drawdown: Equal Weight tiene {abs(diff_dd):.2f}% MÁS caída")

# CONCLUSIONES
print("\n" + "="*80)
print("CONCLUSIONES PROFESIONALES")
print("="*80)

print("\n1. DISTRIBUCIÓN DE RIESGO:")
print("   Equal Weight (33/33/33):")
print("   • TSLA contribuye 51.7% del riesgo (¡más de la mitad!)")
print("   • Portfolio dominado por una sola acción volátil")
print("")
print("   Risk Parity:")
print("   • Cada acción contribuye ~33% del riesgo")
print("   • Riesgo distribuido uniformemente")
print("   • TSLA solo 18.90% del capital (vs 33.33% en equal weight)")

print("\n2. TRADE-OFF RETORNO vs RIESGO:")
print(f"   • Equal Weight: +{retorno_equal:.2f}% retorno, pero drawdown {max_dd_equal:.2f}%")
print(f"   • Risk Parity: +{retorno_rp:.2f}% retorno, drawdown {max_dd_rp:.2f}%")
print(f"   • Sacrificas {diff_retorno:.2f}% de retorno para reducir drawdown en {abs(diff_dd):.2f}%")

print("\n3. SHARPE RATIO (eficiencia):")
print(f"   • Equal Weight: {sharpe_equal:.3f}")
print(f"   • Risk Parity: {sharpe_rp:.3f}")
if sharpe_equal > sharpe_rp:
    print(f"   • Equal Weight es MÁS eficiente por {diff_sharpe:.3f}")
else:
    print(f"   • Risk Parity es MÁS eficiente por {abs(diff_sharpe):.3f}")

print("\n4. PROTECCIÓN EN CRASHES:")
print("   Si TSLA cae -50% (muy probable dado su volatilidad):")
print(f"     • Equal Weight: Pierde ~{33.33 * 0.5:.1f}% = -16.7% del portfolio")
print(f"     • Risk Parity: Pierde ~{18.90 * 0.5:.1f}% = -9.5% del portfolio")
print("   ¡Risk Parity pierde 43% MENOS!")

print("\n5. ¿CUÁNDO USAR CADA ESTRATEGIA?")
print("\n   USAR EQUAL WEIGHT si:")
print("   ✅ Quieres maximizar retorno absoluto")
print("   ✅ Puedes tolerar caídas de -60%+")
print("   ✅ Crees que todas las acciones subirán similarmente")
print("   ✅ Inversión corto plazo (<3 años)")
print("\n   USAR RISK PARITY si:")
print("   ✅ Quieres maximizar Sharpe (retorno/riesgo)")
print("   ✅ No puedes tolerar caídas >-40%")
print("   ✅ Tienes acciones de volatilidades muy diferentes")
print("   ✅ Inversión largo plazo (>5 años)")
print("   ✅ Portfolio con bonos + acciones (volatilidades muy distintas)")

print("\n6. USADO POR:")
print("   • Bridgewater Associates (Ray Dalio): $150B AUM")
print("   • AQR Capital Management")
print("   • Fondos de pensiones institucionales")
print("   • Endowments universitarios (Harvard, Yale)")

print("\n" + "="*80)