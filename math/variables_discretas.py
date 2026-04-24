from scipy.stats import binom, poisson
import numpy as np

# === BINOMIAL: moneda justa ===
print("=== BINOMIAL: Moneda justa, 10 tiradas ===")
N = 10
p = 0.5

# Probabilidad exacta de sacar 7 caras
P_7 = binom.pmf(7, N, p)
print(f"P(exactamente 7 caras) = {P_7:.4f}")

# Probabilidad de sacar 7 o más
P_7_o_mas = 1 - binom.cdf(6, N, p)
print(f"P(7 o más caras) = {P_7_o_mas:.4f}")

# Media y varianza
print(f"Media esperada: {N*p}")
print(f"Varianza: {N*p*(1-p)}")


# === BINOMIAL: tu bot ===
print("\n=== BINOMIAL: Bot con 55% acierto, 20 operaciones ===")
N = 20
p = 0.55

P_15 = binom.pmf(15, N, p)
print(f"P(exactamente 15 aciertos) = {P_15:.4f}")

# Probabilidad de ganar dinero (al menos 11 aciertos de 20)
P_11_o_mas = 1 - binom.cdf(10, N, p)
print(f"P(11 o más aciertos = ganar dinero) = {P_11_o_mas:.4f}")

print(f"Media esperada de aciertos: {N*p}")


# === POISSON: crashes de mercado ===
print("\n=== POISSON: 2 crashes/década ===")
lam = 2

P_3 = poisson.pmf(3, lam)
print(f"P(exactamente 3 crashes en la década) = {P_3:.4f}")

P_0 = poisson.pmf(0, lam)
print(f"P(ningún crash en la década) = {P_0:.4f}")