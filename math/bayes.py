# EJEMPLO 1: Test médico con Bayes
print("=== TEST MÉDICO ===")
P_enfermo = 0.01
P_positivo_dado_enfermo = 0.99
P_positivo_dado_sano = 0.05

P_sano = 1 - P_enfermo

# Probabilidad total de dar positivo
P_positivo = (P_positivo_dado_enfermo * P_enfermo + 
              P_positivo_dado_sano * P_sano)

# Bayes
P_enfermo_dado_positivo = (P_positivo_dado_enfermo * P_enfermo) / P_positivo

print(f"P(enfermo) = {P_enfermo}")
print(f"P(positivo | enfermo) = {P_positivo_dado_enfermo}")
print(f"P(positivo | sano) = {P_positivo_dado_sano}")
print(f"P(positivo) = {P_positivo:.4f}")
print(f"P(enfermo | positivo) = {P_enfermo_dado_positivo:.4f}")
print(f"→ Solo el {P_enfermo_dado_positivo*100:.1f}% de los positivos están realmente enfermos")


# EJEMPLO 2: ML como filtro en trading
print("\n=== ML FILTRO TRADING ===")
P_ML_compra_dado_sube = 0.70  # ML acierta 70% de subidas
P_ML_compra_dado_baja = 0.30  # 30% falsos positivos
P_sube = 0.55  # Mercado sube el 55% de los días

P_baja = 1 - P_sube

P_ML_compra = (P_ML_compra_dado_sube * P_sube + 
               P_ML_compra_dado_baja * P_baja)

P_sube_dado_ML = (P_ML_compra_dado_sube * P_sube) / P_ML_compra

print(f"P(sube | ML dice comprar) = {P_sube_dado_ML:.4f}")
print(f"→ Cuando ML dice comprar, el mercado sube {P_sube_dado_ML*100:.1f}% de las veces")