# Ejemplo 1: Probabilidad con un dado
espacio_muestral = [1, 2, 3, 4, 5, 6]

# Evento A: sacar par
evento_A = [x for x in espacio_muestral if x % 2 == 0]
P_A = len(evento_A) / len(espacio_muestral)
print(f"P(sacar par) = {P_A}")  # 0.5

# Evento B: sacar mayor que 3
evento_B = [x for x in espacio_muestral if x > 3]
P_B = len(evento_B) / len(espacio_muestral)
print(f"P(sacar > 3) = {P_B}")  # 0.5

# Intersección (los que están en ambos)
interseccion = [x for x in evento_A if x in evento_B]
P_interseccion = len(interseccion) / len(espacio_muestral)
print(f"P(par Y >3) = {P_interseccion}")  # 0.333

# Regla de la suma con eventos NO excluyentes
P_A_o_B = P_A + P_B - P_interseccion
print(f"P(par O >3) = {P_A_o_B}")  # 0.666


# Ejemplo 2: Aplicado al trading
print("\n--- TRADING ---")
P_golden_cross = 0.30
P_rsi_sobrevendido = 0.20
P_ambas = 0.05

P_al_menos_una = P_golden_cross + P_rsi_sobrevendido - P_ambas
print(f"P(al menos 1 señal alcista) = {P_al_menos_una}")  # 0.45