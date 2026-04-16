"""
DÍA 41: Machine Learning para Finanzas — Fundamentos
=====================================================
Bootcamp Quant Trading - Irene Tanarro

Modelo: Random Forest Classifier
Target: ¿Sube AAPL mañana? (1 = sí, 0 = no)
Features: Indicadores técnicos (MA, RSI, MACD, volatilidad, volumen)

Requisitos: pip install scikit-learn yfinance pandas numpy
"""

import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)
import warnings
warnings.filterwarnings("ignore")


# ============================================================
# PARTE 1: DESCARGAR DATOS
# ============================================================

print("=" * 60)
print("  🤖 DÍA 41: MACHINE LEARNING PARA FINANZAS")
print("  📊 Modelo: Random Forest — Predicción de AAPL")
print("=" * 60)

print("\n📥 Descargando datos de AAPL (5 años)...")

ticker = "AAPL"
data = yf.download(ticker, start="2020-01-01", end="2025-12-31", progress=False)

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

print(f"   ✅ {len(data)} días de datos descargados")
print(f"   📅 Desde {data.index[0].strftime('%Y-%m-%d')} hasta {data.index[-1].strftime('%Y-%m-%d')}")


# ============================================================
# PARTE 2: FEATURE ENGINEERING
# ============================================================

print("\n🔧 Creando features (variables predictivas)...")

df = data.copy()

# Retornos
df["return_1d"] = df["Close"].pct_change(1)
df["return_5d"] = df["Close"].pct_change(5)
df["return_10d"] = df["Close"].pct_change(10)
df["return_20d"] = df["Close"].pct_change(20)

# Medias Móviles — ratio precio/media
df["MA5"] = df["Close"].rolling(5).mean()
df["MA10"] = df["Close"].rolling(10).mean()
df["MA20"] = df["Close"].rolling(20).mean()
df["MA50"] = df["Close"].rolling(50).mean()

df["precio_vs_MA5"] = df["Close"] / df["MA5"]
df["precio_vs_MA10"] = df["Close"] / df["MA10"]
df["precio_vs_MA20"] = df["Close"] / df["MA20"]
df["precio_vs_MA50"] = df["Close"] / df["MA50"]

# Volatilidad
df["volatilidad_5d"] = df["return_1d"].rolling(5).std()
df["volatilidad_10d"] = df["return_1d"].rolling(10).std()
df["volatilidad_20d"] = df["return_1d"].rolling(20).std()

# RSI
delta = df["Close"].diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss
df["RSI"] = 100 - (100 / (1 + rs))

# MACD
ema12 = df["Close"].ewm(span=12).mean()
ema26 = df["Close"].ewm(span=26).mean()
df["MACD"] = ema12 - ema26
df["MACD_signal"] = df["MACD"].ewm(span=9).mean()
df["MACD_hist"] = df["MACD"] - df["MACD_signal"]

# Volumen relativo
df["volumen_vs_media"] = df["Volume"] / df["Volume"].rolling(20).mean()

# Rango del día
df["rango_diario"] = (df["High"] - df["Low"]) / df["Close"]

# Gap de apertura
df["gap_apertura"] = (df["Open"] - df["Close"].shift(1)) / df["Close"].shift(1)

# Posición en rango de 20 días
df["pos_rango_20d"] = (df["Close"] - df["Low"].rolling(20).min()) / \
                       (df["High"].rolling(20).max() - df["Low"].rolling(20).min())

# Día de la semana
df["dia_semana"] = df.index.dayofweek

print(f"   ✅ 20+ features creadas")


# ============================================================
# PARTE 3: CREAR TARGET
# ============================================================

print("\n🎯 Creando target (variable a predecir)...")

df["target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)

n_sube = df["target"].sum()
n_baja = len(df) - n_sube
print(f"   📈 Días que subió: {n_sube} ({n_sube/len(df)*100:.1f}%)")
print(f"   📉 Días que bajó:  {n_baja} ({n_baja/len(df)*100:.1f}%)")


# ============================================================
# PARTE 4: PREPARAR DATOS PARA ML
# ============================================================

print("\n📦 Preparando datos para el modelo...")

features = [
    "return_1d", "return_5d", "return_10d", "return_20d",
    "precio_vs_MA5", "precio_vs_MA10", "precio_vs_MA20", "precio_vs_MA50",
    "volatilidad_5d", "volatilidad_10d", "volatilidad_20d",
    "RSI", "MACD", "MACD_signal", "MACD_hist",
    "volumen_vs_media", "rango_diario", "gap_apertura",
    "pos_rango_20d", "dia_semana"
]

df_clean = df.dropna(subset=features + ["target"]).copy()
print(f"   📊 Datos limpios: {len(df_clean)} filas (eliminadas {len(df) - len(df_clean)} con NaN)")

# Split temporal (80/20)
split_index = int(len(df_clean) * 0.8)

train = df_clean.iloc[:split_index]
test = df_clean.iloc[split_index:]

X_train = train[features]
y_train = train["target"]
X_test = test[features]
y_test = test["target"]

print(f"\n   📚 ENTRENAMIENTO: {train.index[0].strftime('%Y-%m-%d')} a {train.index[-1].strftime('%Y-%m-%d')} ({len(train)} filas)")
print(f"   🧪 TEST: {test.index[0].strftime('%Y-%m-%d')} a {test.index[-1].strftime('%Y-%m-%d')} ({len(test)} filas)")


# ============================================================
# PARTE 5: ENTRENAR RANDOM FOREST
# ============================================================

print("\n🌲 Entrenando Random Forest...")

modelo = RandomForestClassifier(
    n_estimators=200,
    max_depth=5,
    min_samples_split=20,
    min_samples_leaf=10,
    random_state=42,
    n_jobs=-1
)

modelo.fit(X_train, y_train)
print("   ✅ Modelo entrenado")


# ============================================================
# PARTE 6: EVALUAR MODELO
# ============================================================

print("\n📊 EVALUACIÓN DEL MODELO")
print("=" * 50)

pred_train = modelo.predict(X_train)
pred_test = modelo.predict(X_test)

acc_train = accuracy_score(y_train, pred_train)
acc_test = accuracy_score(y_test, pred_test)

print(f"\n   🎯 Accuracy:")
print(f"      Train: {acc_train:.4f} ({acc_train*100:.2f}%)")
print(f"      Test:  {acc_test:.4f} ({acc_test*100:.2f}%)")

diff = acc_train - acc_test
if diff > 0.10:
    print(f"      ⚠️ Diferencia: {diff:.4f} → POSIBLE OVERFITTING")
elif diff > 0.05:
    print(f"      🟡 Diferencia: {diff:.4f} → Algo de overfitting, aceptable")
else:
    print(f"      ✅ Diferencia: {diff:.4f} → Bien generalizado")

prec_test = precision_score(y_test, pred_test, zero_division=0)
rec_test = recall_score(y_test, pred_test, zero_division=0)
f1_test = f1_score(y_test, pred_test, zero_division=0)

print(f"\n   📈 Métricas detalladas (TEST):")
print(f"      Precision: {prec_test:.4f}")
print(f"      Recall:    {rec_test:.4f}")
print(f"      F1 Score:  {f1_test:.4f}")

cm = confusion_matrix(y_test, pred_test)
print(f"\n   📋 Matriz de Confusión (TEST):")
print(f"                    Predicho BAJA  Predicho SUBE")
print(f"      Real BAJA:        {cm[0][0]:>5}          {cm[0][1]:>5}")
print(f"      Real SUBE:        {cm[1][0]:>5}          {cm[1][1]:>5}")

total_test = len(y_test)
aciertos = cm[0][0] + cm[1][1]
fallos = cm[0][1] + cm[1][0]
print(f"\n      ✅ Aciertos: {aciertos} ({aciertos/total_test*100:.1f}%)")
print(f"      ❌ Fallos:   {fallos} ({fallos/total_test*100:.1f}%)")

baseline = y_test.mean()
print(f"\n   📏 Comparación con BASELINE:")
print(f"      Baseline (siempre 'sube'): {baseline*100:.2f}%")
print(f"      Tu modelo:                 {acc_test*100:.2f}%")
mejora = acc_test - baseline
if mejora > 0:
    print(f"      ✅ Modelo supera baseline por {mejora*100:.2f} pp")
else:
    print(f"      ⚠️ Modelo no supera baseline. Normal con primer modelo.")


# ============================================================
# PARTE 7: FEATURES MÁS IMPORTANTES
# ============================================================

print("\n🏆 TOP 10 FEATURES MÁS IMPORTANTES")
print("=" * 50)

importancias = pd.Series(
    modelo.feature_importances_,
    index=features
).sort_values(ascending=False)

for i, (feat, imp) in enumerate(importancias.head(10).items()):
    barra = "█" * int(imp * 100)
    print(f"   {i+1:>2}. {feat:<20} {imp:.4f}  {barra}")


# ============================================================
# PARTE 8: SIMULAR TRADING CON ML
# ============================================================

print("\n💰 SIMULACIÓN DE TRADING CON ML")
print("=" * 50)

sim = test.copy()
sim["prediccion"] = pred_test

sim["retorno_ml"] = sim["return_1d"].shift(-1) * sim["prediccion"]
sim["retorno_bh"] = sim["return_1d"].shift(-1)

sim["acum_ml"] = (1 + sim["retorno_ml"]).cumprod()
sim["acum_bh"] = (1 + sim["retorno_bh"]).cumprod()

retorno_ml = (sim["acum_ml"].iloc[-2] - 1) * 100
retorno_bh = (sim["acum_bh"].iloc[-2] - 1) * 100

print(f"\n   📊 Rendimiento en período de TEST:")
print(f"      🤖 Estrategia ML:     {retorno_ml:>+8.2f}%")
print(f"      📈 Buy & Hold:        {retorno_bh:>+8.2f}%")

if retorno_ml > retorno_bh:
    print(f"\n   ✅ ML GANÓ por {retorno_ml - retorno_bh:.2f} pp")
elif retorno_ml > 0:
    print(f"\n   🟡 ML ganó dinero pero no superó B&H ({retorno_ml - retorno_bh:.2f} pp)")
else:
    print(f"\n   ⚠️ ML perdió dinero. Normal con primer modelo sin optimizar.")

dias_invertido = sim["prediccion"].sum()
dias_total = len(sim)
print(f"\n   📅 Días invertido: {dias_invertido:.0f} de {dias_total} ({dias_invertido/dias_total*100:.1f}%)")

retornos_ml = sim["retorno_ml"].dropna()
if retornos_ml.std() > 0:
    sharpe_ml = (retornos_ml.mean() / retornos_ml.std()) * np.sqrt(252)
    print(f"   📐 Sharpe Ratio ML: {sharpe_ml:.4f}")

retornos_bh = sim["retorno_bh"].dropna()
if retornos_bh.std() > 0:
    sharpe_bh = (retornos_bh.mean() / retornos_bh.std()) * np.sqrt(252)
    print(f"   📐 Sharpe Ratio B&H: {sharpe_bh:.4f}")


# ============================================================
# PARTE 9: PREDICCIÓN PARA HOY
# ============================================================

print("\n" + "=" * 50)
print("🔮 PREDICCIÓN PARA EL PRÓXIMO DÍA DE TRADING")
print("=" * 50)

ultimo_dia = df_clean[features].iloc[-1:]
prediccion_hoy = modelo.predict(ultimo_dia)[0]
probabilidad = modelo.predict_proba(ultimo_dia)[0]
fecha_ultimo = df_clean.index[-1].strftime("%Y-%m-%d")

print(f"\n   📅 Basado en datos del: {fecha_ultimo}")
print(f"   🎯 Predicción: {'📈 SUBE' if prediccion_hoy == 1 else '📉 BAJA'}")
print(f"   📊 Prob. subir: {probabilidad[1]*100:.1f}%")
print(f"   📊 Prob. bajar: {probabilidad[0]*100:.1f}%")

confianza = max(probabilidad)
if confianza > 0.65:
    print(f"   🟢 Confianza: ALTA ({confianza*100:.1f}%)")
elif confianza > 0.55:
    print(f"   🟡 Confianza: MEDIA ({confianza*100:.1f}%)")
else:
    print(f"   🔴 Confianza: BAJA ({confianza*100:.1f}%) — No operar")

print(f"\n   💡 Señal de trading:")
if prediccion_hoy == 1 and confianza > 0.55:
    print(f"      ✅ COMPRAR — Predicción subida con {confianza*100:.1f}% confianza")
elif prediccion_hoy == 0 and confianza > 0.55:
    print(f"      🔴 NO COMPRAR / VENDER — Predicción bajada")
else:
    print(f"      ⏸️ ESPERAR — Confianza insuficiente")


# ============================================================
# PARTE 10: RESUMEN
# ============================================================

print("\n" + "=" * 60)
print("  ✅ DÍA 41 COMPLETADO")
print("=" * 60)
