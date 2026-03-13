import yfinance as yf
import pandas as pd
import math

ticker = "AAPL"
data = yf.download(ticker, start="2020-01-01", group_by='ticker')

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.droplevel(0)

print("\n" + "="*70)
print("OPTIMIZACION DE PARAMETROS - MEDIAS MOVILES")
print("="*70)

# Dividir en Train y Test
train_data = data['2020':'2023'].copy()
test_data = data['2024':'2026'].copy()

# Función para simular estrategia con parámetros específicos
def simular_con_parametros(data_periodo, ma_corto, ma_largo):
    data_sim = data_periodo.copy()
    
    data_sim['MA_Corto'] = data_sim['Close'].rolling(window=ma_corto).mean()
    data_sim['MA_Largo'] = data_sim['Close'].rolling(window=ma_largo).mean()
    data_sim['Signal'] = 0
    data_sim.loc[data_sim['MA_Corto'] > data_sim['MA_Largo'], 'Signal'] = 1
    data_sim['Position'] = data_sim['Signal'].diff()
    
    capital = 10000.0
    shares = 0.0
    
    for i in range(len(data_sim)):
        pos = data_sim['Position'].values[i]
        precio = data_sim['Close'].values[i]
        
        if pos == 1.0 and shares == 0.0:
            shares = capital / precio
        elif pos == -1.0 and shares > 0.0:
            capital = shares * precio
            shares = 0.0
    
    # Venta final
    if shares > 0.0:
        precio_final = data_sim['Close'].values[-1]
        capital = shares * precio_final
    
    if hasattr(capital, 'item'):
        capital = capital.item()
    
    if math.isnan(capital):
        capital = 10000.0
    
    retorno = ((capital / 10000) - 1) * 100
    
    return retorno

# GRID SEARCH en Train
print("\n[FASE 1] OPTIMIZACION EN TRAIN (2020-2023)")
print("-" * 70)
print("Probando combinaciones de MA corto y MA largo...")

ma_cortos = [5, 10, 15, 20, 25, 30]
ma_largos = [20, 30, 40, 50, 60, 70, 80, 90, 100]

resultados = []

for ma_c in ma_cortos:
    for ma_l in ma_largos:
        # Solo probar si MA corto < MA largo
        if ma_c < ma_l:
            retorno_train = simular_con_parametros(train_data, ma_c, ma_l)
            resultados.append({
                'ma_corto': ma_c,
                'ma_largo': ma_l,
                'retorno_train': retorno_train
            })

# Ordenar por retorno en train
resultados_ordenados = sorted(resultados, key=lambda x: x['retorno_train'], reverse=True)

print(f"\nTotal de combinaciones probadas: {len(resultados_ordenados)}")

print("\nTOP 10 MEJORES COMBINACIONES EN TRAIN:")
print("-" * 70)
for i in range(min(10, len(resultados_ordenados))):
    r = resultados_ordenados[i]
    print(f"{i+1}. MA{r['ma_corto']}/MA{r['ma_largo']} → Train: +{round(r['retorno_train'], 2)}%")

# Probar el top 5 en TEST
print("\n" + "="*70)
print("[FASE 2] VALIDACION EN TEST (2024-2026)")
print("="*70)
print("\nProbando las 5 mejores combinaciones en datos NUNCA VISTOS...")

print("\nRESULTADOS:")
print("-" * 70)

for i in range(min(5, len(resultados_ordenados))):
    r = resultados_ordenados[i]
    ma_c = r['ma_corto']
    ma_l = r['ma_largo']
    retorno_train = r['retorno_train']
    
    # Probar en test
    retorno_test = simular_con_parametros(test_data, ma_c, ma_l)
    
    degradacion = retorno_train - retorno_test
    
    print(f"\n{i+1}. MA{ma_c}/MA{ma_l}")
    print(f"   Train: +{round(retorno_train, 2)}%")
    print(f"   Test:  +{round(retorno_test, 2)}%")
    print(f"   Degradacion: {round(degradacion, 2)}%")
    
    if degradacion < 10:
        print(f"   Calificacion: EXCELENTE - Muy robusta")
    elif degradacion < 30:
        print(f"   Calificacion: BUENA - Robusta")
    elif degradacion < 50:
        print(f"   Calificacion: ACEPTABLE - Algo de overfitting")
    else:
        print(f"   Calificacion: MALA - Mucho overfitting")

# Comparar con MA20/MA50 (nuestra baseline)
print("\n" + "="*70)
print("COMPARACION CON MA20/MA50 (BASELINE)")
print("="*70)

retorno_baseline_train = simular_con_parametros(train_data, 20, 50)
retorno_baseline_test = simular_con_parametros(test_data, 20, 50)
degradacion_baseline = retorno_baseline_train - retorno_baseline_test

print(f"\nMA20/MA50 (baseline):")
print(f"Train: +{round(retorno_baseline_train, 2)}%")
print(f"Test:  +{round(retorno_baseline_test, 2)}%")
print(f"Degradacion: {round(degradacion_baseline, 2)}%")

# Mejor combinación
mejor = resultados_ordenados[0]
retorno_mejor_test = simular_con_parametros(test_data, mejor['ma_corto'], mejor['ma_largo'])

print(f"\nMejor combinación (MA{mejor['ma_corto']}/MA{mejor['ma_largo']}):")
print(f"Train: +{round(mejor['retorno_train'], 2)}%")
print(f"Test:  +{round(retorno_mejor_test, 2)}%")

mejora_train = mejor['retorno_train'] - retorno_baseline_train
mejora_test = retorno_mejor_test - retorno_baseline_test

print(f"\nMejora vs baseline:")
print(f"En Train: +{round(mejora_train, 2)}% puntos")
print(f"En Test:  +{round(mejora_test, 2)}% puntos")

if mejora_test > 10:
    print("\nCONCLUSION: La optimizacion encontro parametros SIGNIFICATIVAMENTE mejores")
elif mejora_test > 5:
    print("\nCONCLUSION: La optimizacion encontro parametros MODERADAMENTE mejores")
elif mejora_test > 0:
    print("\nCONCLUSION: Mejora pequeña - probablemente ruido, usa MA20/MA50")
else:
    print("\nCONCLUSION: MA20/MA50 sigue siendo la mejor opcion (overfitting en optimizacion)")

print("="*70)