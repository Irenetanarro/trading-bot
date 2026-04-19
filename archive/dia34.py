import yfinance as yf
import pandas as pd
import numpy as np
from scipy import stats

# Descargar datos
print("\n" + "="*80)
print("VaR (VALUE AT RISK) - AAPL + MSFT + TSLA")
print("="*80)
print("\nDescargando datos...\n")

tickers = ["AAPL", "MSFT", "TSLA"]
data = yf.download(tickers, start="2020-01-01", end="2026-04-03", progress=False)['Close']

# Calcular retornos diarios
returns = data.pct_change().dropna()

# Función para calcular VaR
def calcular_var(returns_series, nivel_confianza=0.95, horizonte_dias=1):
    """
    Calcula VaR usando método histórico
    
    nivel_confianza: 0.90, 0.95, 0.99
    horizonte_dias: 1, 5, 10, etc.
    """
    # Ajustar retornos por horizonte temporal
    if horizonte_dias > 1:
        returns_horizonte = returns_series.rolling(window=horizonte_dias).sum().dropna()
    else:
        returns_horizonte = returns_series
    
    # VaR es el percentil correspondiente
    var_percentil = 1 - nivel_confianza
    var = returns_horizonte.quantile(var_percentil)
    
    return var * 100  # Retornar en porcentaje

# PARTE 1: VaR INDIVIDUAL DE CADA ACCIÓN
print("="*80)
print("PARTE 1: VaR INDIVIDUAL DE CADA ACCIÓN")
print("="*80)

print("\nVaR 1-día al 95% (estándar industria):")
print("-" * 50)

vars_individuales_1d = {}
for ticker in tickers:
    var_95 = calcular_var(returns[ticker], nivel_confianza=0.95, horizonte_dias=1)
    vars_individuales_1d[ticker] = var_95
    print(f"{ticker}: {var_95:.2f}%")
    print(f"  Interpretación: 19 de 20 días, pérdida < {abs(var_95):.2f}%")
    print(f"                  1 de 20 días, pérdida > {abs(var_95):.2f}%")
    print()

print("\nVaR 10-días al 95%:")
print("-" * 50)

vars_individuales_10d = {}
for ticker in tickers:
    var_95_10d = calcular_var(returns[ticker], nivel_confianza=0.95, horizonte_dias=10)
    vars_individuales_10d[ticker] = var_95_10d
    print(f"{ticker}: {var_95_10d:.2f}%")
    print(f"  Interpretación: En ventanas de 10 días, 95% del tiempo pérdida < {abs(var_95_10d):.2f}%")
    print()

# Comparar niveles de confianza para TSLA
print("\n" + "="*80)
print("COMPARACIÓN: DIFERENTES NIVELES DE CONFIANZA (TSLA)")
print("="*80 + "\n")

for confianza in [0.90, 0.95, 0.99]:
    var_tsla = calcular_var(returns['TSLA'], nivel_confianza=confianza, horizonte_dias=1)
    dias_seguros = int(confianza * 100)
    dias_malos = 100 - dias_seguros
    print(f"VaR 1-día al {int(confianza*100)}%: {var_tsla:.2f}%")
    print(f"  → {dias_seguros} de 100 días seguros, {dias_malos} días malos")
    print()

# PARTE 2: VaR DE PORTFOLIOS
print("="*80)
print("PARTE 2: VaR DE PORTFOLIOS (Equal Weight vs Risk Parity)")
print("="*80)

# Equal Weight: 33.33% cada uno
pesos_equal = np.array([1/3, 1/3, 1/3])

# Risk Parity: calcular pesos
volatilidades = returns.std() * np.sqrt(252)
inv_vols = 1 / volatilidades
pesos_rp = inv_vols / inv_vols.sum()

print("\nPesos de cada estrategia:")
print("-" * 50)
print("Equal Weight:")
for i, ticker in enumerate(tickers):
    print(f"  {ticker}: {pesos_equal[i]*100:.2f}%")

print("\nRisk Parity:")
for i, ticker in enumerate(tickers):
    print(f"  {ticker}: {pesos_rp.iloc[i]*100:.2f}%")

# Calcular retornos del portfolio
returns_equal = (returns * pesos_equal).sum(axis=1)
returns_rp = (returns * pesos_rp.values).sum(axis=1)

# VaR de portfolios
print("\n" + "="*80)
print("VaR DE PORTFOLIOS - 1 DÍA AL 95%")
print("="*80 + "\n")

var_equal_1d = calcular_var(returns_equal, nivel_confianza=0.95, horizonte_dias=1)
var_rp_1d = calcular_var(returns_rp, nivel_confianza=0.95, horizonte_dias=1)

print(f"Equal Weight (33/33/33): {var_equal_1d:.2f}%")
print(f"Risk Parity: {var_rp_1d:.2f}%")

diferencia = abs(var_equal_1d) - abs(var_rp_1d)
print(f"\nDiferencia: {diferencia:.2f}% {'mayor riesgo en Equal Weight' if diferencia > 0 else 'menor riesgo en Equal Weight'}")

# Calcular "suma ingenua" de VaRs individuales
var_suma_ingenua = sum(vars_individuales_1d[t] * pesos_equal[i] for i, t in enumerate(tickers))
print(f"\n⚠️  Si sumáramos VaRs individuales (INCORRECTO): {var_suma_ingenua:.2f}%")
print(f"✅  VaR real del portfolio: {var_equal_1d:.2f}%")
print(f"🎯  Beneficio de diversificación: {abs(var_suma_ingenua - var_equal_1d):.2f}%")

# VaR 10-días
print("\n" + "="*80)
print("VaR DE PORTFOLIOS - 10 DÍAS AL 95%")
print("="*80 + "\n")

var_equal_10d = calcular_var(returns_equal, nivel_confianza=0.95, horizonte_dias=10)
var_rp_10d = calcular_var(returns_rp, nivel_confianza=0.95, horizonte_dias=10)

print(f"Equal Weight: {var_equal_10d:.2f}%")
print(f"Risk Parity: {var_rp_10d:.2f}%")

# TRADUCCIÓN A DÓLARES
print("\n" + "="*80)
print("VaR EN DÓLARES (Portfolio de $10,000)")
print("="*80 + "\n")

capital = 10000

print("VaR 1-día al 95%:")
print(f"  Equal Weight: ${int(capital * abs(var_equal_1d/100)):,}")
print(f"    → 19 de 20 días, pérdida < ${int(capital * abs(var_equal_1d/100)):,}")
print(f"  Risk Parity: ${int(capital * abs(var_rp_1d/100)):,}")
print(f"    → 19 de 20 días, pérdida < ${int(capital * abs(var_rp_1d/100)):,}")

print("\nVaR 10-días al 95%:")
print(f"  Equal Weight: ${int(capital * abs(var_equal_10d/100)):,}")
print(f"  Risk Parity: ${int(capital * abs(var_rp_10d/100)):,}")

# COMPARACIÓN COMPLETA
print("\n" + "="*80)
print("TABLA COMPARATIVA COMPLETA")
print("="*80 + "\n")

resultados = pd.DataFrame({
    'Métrica': [
        'VaR 1-día 95%',
        'VaR 10-días 95%',
        'VaR 1-día 99%'
    ],
    'Equal Weight': [
        f"{var_equal_1d:.2f}%",
        f"{var_equal_10d:.2f}%",
        f"{calcular_var(returns_equal, 0.99, 1):.2f}%"
    ],
    'Risk Parity': [
        f"{var_rp_1d:.2f}%",
        f"{var_rp_10d:.2f}%",
        f"{calcular_var(returns_rp, 0.99, 1):.2f}%"
    ]
})

print(resultados.to_string(index=False))

# ANÁLISIS Y CONCLUSIONES
print("\n" + "="*80)
print("ANÁLISIS Y CONCLUSIONES")
print("="*80)

print("\n1. ORDENAMIENTO POR RIESGO (VaR 1-día):")
vars_sorted = sorted(vars_individuales_1d.items(), key=lambda x: x[1])
for i, (ticker, var) in enumerate(vars_sorted, 1):
    print(f"   {i}. {ticker}: {var:.2f}% {'(menos riesgosa)' if i == 1 else '(más riesgosa)' if i == len(vars_sorted) else ''}")

print("\n2. BENEFICIO DE DIVERSIFICACIÓN:")
print(f"   • VaR individual promedio: {np.mean(list(vars_individuales_1d.values())):.2f}%")
print(f"   • VaR Equal Weight: {var_equal_1d:.2f}%")
print(f"   • Reducción de riesgo: {abs(np.mean(list(vars_individuales_1d.values())) - var_equal_1d):.2f}%")

print("\n3. EQUAL WEIGHT vs RISK PARITY:")
if abs(var_equal_1d) > abs(var_rp_1d):
    print(f"   ✅ Risk Parity tiene MENOR VaR ({abs(var_rp_1d):.2f}% vs {abs(var_equal_1d):.2f}%)")
    print(f"   → Risk Parity es {((abs(var_equal_1d) - abs(var_rp_1d)) / abs(var_equal_1d) * 100):.1f}% menos riesgoso")
else:
    print(f"   ✅ Equal Weight tiene MENOR VaR ({abs(var_equal_1d):.2f}% vs {abs(var_rp_1d):.2f}%)")

print("\n4. INTERPRETACIÓN PRÁCTICA:")
print(f"   Con $10,000 en Equal Weight:")
print(f"   • 19 de 20 días: Pérdida < ${int(capital * abs(var_equal_1d/100)):,}")
print(f"   • 1 de 20 días: Pérdida > ${int(capital * abs(var_equal_1d/100)):,}")
print(f"   • En un mes (20 días trading): Espera 1 día con pérdida >{abs(var_equal_1d):.2f}%")

print("\n5. LIMITACIONES DE VaR:")
print("   ⚠️  VaR NO dice cuánto pierdes en el 5% peor de casos")
print("   ⚠️  Solo dice que el 95% del tiempo pierdes menos de X")
print("   ⚠️  En el 5% restante, podrías perder -20%, -50%, -80%")
print("   ⚠️  Por eso los reguladores también requieren CVaR (Conditional VaR)")

print("\n6. USADO POR:")
print("   • JP Morgan (inventó VaR en 1994)")
print("   • Todos los bancos (requerimiento Basel III)")
print("   • SEC, FINRA (reguladores)")
print("   • Hedge funds para reportar riesgo")
print("   • Gestoras de fondos de pensiones")

print("\n" + "="*80)