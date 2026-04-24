import numpy as np
from scipy.stats import norm, lognorm
import matplotlib.pyplot as plt
import yfinance as yf

# === PARTE 1: Distribución Normal básica ===
print("=== DISTRIBUCIÓN NORMAL ===")

# Crear una distribución con media 0 y std 1 (Normal estándar)
media = 0
std = 1

# Probabilidad de que un valor sea menor que 1
P_menor_1 = norm.cdf(1, media, std)
print(f"P(X < 1) = {P_menor_1:.4f}")  # 0.8413

# Probabilidad entre -1 y 1 (regla del 68%)
P_entre_m1_y_1 = norm.cdf(1, media, std) - norm.cdf(-1, media, std)
print(f"P(-1 < X < 1) = {P_entre_m1_y_1:.4f}")  # ~0.68

# Regla del 95% (entre -2 y 2)
P_95 = norm.cdf(2, media, std) - norm.cdf(-2, media, std)
print(f"P(-2 < X < 2) = {P_95:.4f}")  # ~0.95


# === PARTE 2: Retornos de AAPL ===
print("\n=== RETORNOS DE AAPL ===")

data = yf.download("AAPL", period="2y", progress=False)
if data.columns.nlevels > 1:
    data.columns = data.columns.get_level_values(0)

# Calcular retornos diarios en %
data["retorno"] = data["Close"].pct_change() * 100
retornos = data["retorno"].dropna()

# Estadísticas
media_ret = retornos.mean()
std_ret = retornos.std()

print(f"Media de retornos diarios: {media_ret:.4f}%")
print(f"Desviación estándar: {std_ret:.4f}%")

# Regla 68-95-99.7
print(f"\n📊 Reglas de la Normal:")
print(f"68% de los días AAPL se mueve entre {media_ret - std_ret:.2f}% y {media_ret + std_ret:.2f}%")
print(f"95% de los días AAPL se mueve entre {media_ret - 2*std_ret:.2f}% y {media_ret + 2*std_ret:.2f}%")
print(f"99.7% de los días AAPL se mueve entre {media_ret - 3*std_ret:.2f}% y {media_ret + 3*std_ret:.2f}%")


# === PARTE 3: ¿Los retornos son realmente normales? ===
from scipy import stats

# Test de normalidad (Shapiro-Wilk)
estadistico, p_valor = stats.shapiro(retornos.values[:500])
print(f"\nTest de normalidad (Shapiro-Wilk):")
print(f"P-valor: {p_valor:.6f}")
if p_valor < 0.05:
    print("→ Los retornos NO son perfectamente normales")
    print("→ Tienen 'colas gordas': movimientos extremos más frecuentes de lo esperado")
else:
    print("→ Los retornos se ajustan razonablemente a una Normal")