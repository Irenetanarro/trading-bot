import numpy as np

# === EJEMPLO 1: DADO ===
print("=== EXPECTED VALUE: DADO ===")
resultados = [1, 2, 3, 4, 5, 6]
probs = [1/6] * 6

E = sum(r * p for r, p in zip(resultados, probs))
print(f"E(X) = {E:.4f}")

var = sum(p * (r - E)**2 for r, p in zip(resultados, probs))
print(f"Varianza = {var:.4f}")
print(f"Desv. estándar = {np.sqrt(var):.4f}")


# === EJEMPLO 2: BOT CON P(GANAR)=55% ===
print("\n=== BOT v2: Win rate 55% ===")
P_ganar = 0.55
ganancia_media = 5  # en %
P_perder = 0.45
perdida_media = 3  # en %

E = P_ganar * ganancia_media - P_perder * perdida_media
print(f"E(operación) = {E:.2f}%")
print(f"Después de 100 operaciones: +{E*100:.2f}% de retorno aproximado")


# === EJEMPLO 3: LA TRAMPA DEL 80% WIN RATE ===
print("\n=== TRAMPA: Win Rate 80% ===")
P_ganar = 0.80
ganancia_media = 1  # unidad
P_perder = 0.20
perdida_media = 5  # unidades

E = P_ganar * ganancia_media - P_perder * perdida_media
print(f"E = {E:.2f}")
if E > 0:
    print("→ Merece la pena (a largo plazo gana)")
else:
    print("→ NO merece la pena (a largo plazo pierde)")


# === EJEMPLO 4: SIMULACIÓN REAL ===
print("\n=== SIMULACIÓN 10,000 OPERACIONES ===")
np.random.seed(42)

# Estrategia A: bot v2 (55% win, +5% vs -3%)
capital_A = 1000
historico_A = [capital_A]
for _ in range(10000):
    if np.random.random() < 0.55:
        capital_A *= 1.05  # gana 5%
    else:
        capital_A *= 0.97  # pierde 3%
    historico_A.append(capital_A)

# Estrategia B: 80% win pero pérdidas grandes
capital_B = 1000
historico_B = [capital_B]
for _ in range(10000):
    if np.random.random() < 0.80:
        capital_B *= 1.01  # gana 1%
    else:
        capital_B *= 0.95  # pierde 5%
    historico_B.append(capital_B)

print(f"Estrategia A (bot v2): capital final = ${capital_A:.2f}")
print(f"Estrategia B (trampa 80%): capital final = ${capital_B:.2f}")