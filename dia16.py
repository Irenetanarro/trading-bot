import yfinance as yf
import pandas as pd
import math

ticker = "AAPL"
data = yf.download(ticker, start="2020-01-01", group_by='ticker')

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.droplevel(0)

print("\n" + "="*70)
print("WALK-FORWARD TESTING - MEDIAS MOVILES")
print("="*70)

# Calcular medias móviles
data['MA20'] = data['Close'].rolling(window=20).mean()
data['MA50'] = data['Close'].rolling(window=50).mean()
data['Signal_MA'] = 0
data.loc[data['MA20'] > data['MA50'], 'Signal_MA'] = 1
data['Position_MA'] = data['Signal_MA'].diff()

# Función para simular estrategia en un período
def simular_estrategia(data_periodo):
    capital = 10000.0
    shares = 0.0
    
    for i in range(len(data_periodo)):
        pos = data_periodo['Position_MA'].values[i]
        precio = data_periodo['Close'].values[i]
        
        if pos == 1.0 and shares == 0.0:
            shares = capital / precio
        elif pos == -1.0 and shares > 0.0:
            capital = shares * precio
            shares = 0.0
    
    # Venta final
    if shares > 0.0:
        precio_final = data_periodo['Close'].values[-1]
        capital = shares * precio_final
    
    if hasattr(capital, 'item'):
        capital = capital.item()
    
    return capital

# SPLIT 1: Train 2020-2023, Test 2024-2026
print("\n" + "="*70)
print("SPLIT 1: Train en 2020-2023, Test en 2024-2026")
print("="*70)

train_data_1 = data['2020':'2023']
test_data_1 = data['2024':'2026']

# Calcular señales para train
train_data_1 = train_data_1.copy()
train_data_1['MA20'] = train_data_1['Close'].rolling(window=20).mean()
train_data_1['MA50'] = train_data_1['Close'].rolling(window=50).mean()
train_data_1['Signal_MA'] = 0
train_data_1.loc[train_data_1['MA20'] > train_data_1['MA50'], 'Signal_MA'] = 1
train_data_1['Position_MA'] = train_data_1['Signal_MA'].diff()

capital_train_1 = simular_estrategia(train_data_1)
retorno_train_1 = ((capital_train_1 / 10000) - 1) * 100

print("\nTRAIN (2020-2023):")
print("Capital final: $", int(capital_train_1))
print("Retorno: +", round(retorno_train_1, 2), "%")

# Calcular señales para test
test_data_1 = test_data_1.copy()
test_data_1['MA20'] = test_data_1['Close'].rolling(window=20).mean()
test_data_1['MA50'] = test_data_1['Close'].rolling(window=50).mean()
test_data_1['Signal_MA'] = 0
test_data_1.loc[test_data_1['MA20'] > test_data_1['MA50'], 'Signal_MA'] = 1
test_data_1['Position_MA'] = test_data_1['Signal_MA'].diff()

capital_test_1 = simular_estrategia(test_data_1)

if hasattr(capital_test_1, 'item'):
    capital_test_1 = capital_test_1.item()

# Manejar NaN
if math.isnan(capital_test_1):
    capital_test_1 = 10000
    retorno_test_1 = 0
    print("\nTEST (2024-2026) - DATOS NUNCA VISTOS:")
    print("Capital final: $ 10000 (sin operaciones)")
    print("Retorno: 0.0 %")
else:
    retorno_test_1 = ((capital_test_1 / 10000) - 1) * 100
    print("\nTEST (2024-2026) - DATOS NUNCA VISTOS:")
    print("Capital final: $", int(capital_test_1))
    print("Retorno: +", round(retorno_test_1, 2), "%")

degradacion_1 = retorno_train_1 - retorno_test_1
print("\nDegradacion (Train - Test):", round(degradacion_1, 2), "%")

if degradacion_1 < 10:
    print("Resultado: EXCELENTE - Estrategia robusta")
elif degradacion_1 < 30:
    print("Resultado: BUENO - Degradacion aceptable")
elif degradacion_1 < 50:
    print("Resultado: ACEPTABLE - Algo de overfitting")
else:
    print("Resultado: MALO - Mucho overfitting")

# SPLIT 2: Train 2020-2022, Test 2023-2026
print("\n" + "="*70)
print("SPLIT 2: Train en 2020-2022, Test en 2023-2026")
print("="*70)

train_data_2 = data['2020':'2022']
test_data_2 = data['2023':'2026']

# Train
train_data_2 = train_data_2.copy()
train_data_2['MA20'] = train_data_2['Close'].rolling(window=20).mean()
train_data_2['MA50'] = train_data_2['Close'].rolling(window=50).mean()
train_data_2['Signal_MA'] = 0
train_data_2.loc[train_data_2['MA20'] > train_data_2['MA50'], 'Signal_MA'] = 1
train_data_2['Position_MA'] = train_data_2['Signal_MA'].diff()

capital_train_2 = simular_estrategia(train_data_2)
retorno_train_2 = ((capital_train_2 / 10000) - 1) * 100

print("\nTRAIN (2020-2022):")
print("Capital final: $", int(capital_train_2))
print("Retorno: +", round(retorno_train_2, 2), "%")

# Test
test_data_2 = test_data_2.copy()
test_data_2['MA20'] = test_data_2['Close'].rolling(window=20).mean()
test_data_2['MA50'] = test_data_2['Close'].rolling(window=50).mean()
test_data_2['Signal_MA'] = 0
test_data_2.loc[test_data_2['MA20'] > test_data_2['MA50'], 'Signal_MA'] = 1
test_data_2['Position_MA'] = test_data_2['Signal_MA'].diff()

capital_test_2 = simular_estrategia(test_data_2)

if hasattr(capital_test_2, 'item'):
    capital_test_2 = capital_test_2.item()

# Manejar NaN
if math.isnan(capital_test_2):
    capital_test_2 = 10000
    retorno_test_2 = 0
    print("\nTEST (2023-2026) - DATOS NUNCA VISTOS:")
    print("Capital final: $ 10000 (sin operaciones)")
    print("Retorno: 0.0 %")
else:
    retorno_test_2 = ((capital_test_2 / 10000) - 1) * 100
    print("\nTEST (2023-2026) - DATOS NUNCA VISTOS:")
    print("Capital final: $", int(capital_test_2))
    print("Retorno: +", round(retorno_test_2, 2), "%")

degradacion_2 = retorno_train_2 - retorno_test_2
print("\nDegradacion (Train - Test):", round(degradacion_2, 2), "%")

if degradacion_2 < 10:
    print("Resultado: EXCELENTE - Estrategia robusta")
elif degradacion_2 < 30:
    print("Resultado: BUENO - Degradacion aceptable")
elif degradacion_2 < 50:
    print("Resultado: ACEPTABLE - Algo de overfitting")
else:
    print("Resultado: MALO - Mucho overfitting")

# RESUMEN FINAL
print("\n" + "="*70)
print("RESUMEN: ¿LA ESTRATEGIA ES ROBUSTA?")
print("="*70)

print("\nSplit 1 - Degradacion:", round(degradacion_1, 2), "%")
print("Split 2 - Degradacion:", round(degradacion_2, 2), "%")

promedio_degradacion = (degradacion_1 + degradacion_2) / 2
print("\nPromedio de degradacion:", round(promedio_degradacion, 2), "%")

if promedio_degradacion < 10:
    print("\nCONCLUSION: La estrategia es ROBUSTA - Funciona en datos no vistos")
elif promedio_degradacion < 30:
    print("\nCONCLUSION: La estrategia es ACEPTABLE - Algo de overfitting pero usable")
else:
    print("\nCONCLUSION: La estrategia tiene OVERFITTING - No confiar para trading real")

print("\nREFERENCIA:")
print("Degradacion < 10%: Estrategia robusta")
print("Degradacion 10-30%: Aceptable")
print("Degradacion > 30%: Overfitting preocupante")
print("="*70)