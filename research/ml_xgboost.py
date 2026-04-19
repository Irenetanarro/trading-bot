"""
DÍA 42: XGBoost vs Random Forest — Comparación Directa
=======================================================
Bootcamp Quant Trading - Irene Tanarro

Modelo: XGBoost Classifier vs Random Forest
Target: ¿Sube AAPL mañana? (1 = sí, 0 = no)
Objetivo: ¿XGBoost supera el 51.37% de Random Forest?

Requisitos: pip install xgboost scikit-learn yfinance pandas numpy
"""

import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from xgboost import XGBClassifier
import warnings
warnings.filterwarnings("ignore")


# ============================================================
# PARTE 1: DESCARGAR DATOS Y CREAR FEATURES
# ============================================================
# (Mismo proceso que Día 41 — lo reutilizamos)

print("=" * 60)
print("  🚀 DÍA 42: XGBOOST vs RANDOM FOREST")
print("  📊 Comparación directa — mismo dataset, mismos features")
print("=" * 60)

print("\n📥 Descargando datos de AAPL...")

ticker = "AAPL"
data = yf.download(ticker, start="2020-01-01", end="2025-12-31", progress=False)

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

print(f"   ✅ {len(data)} días descargados")

df = data.copy()

# Features (mismo feature engineering que Día 41)
df["return_1d"] = df["Close"].pct_change(1)
df["return_5d"] = df["Close"].pct_change(5)
df["return_10d"] = df["Close"].pct_change(10)
df["return_20d"] = df["Close"].pct_change(20)

df["MA5"] = df["Close"].rolling(5).mean()
df["MA10"] = df["Close"].rolling(10).mean()
df["MA20"] = df["Close"].rolling(20).mean()
df["MA50"] = df["Close"].rolling(50).mean()

df["precio_vs_MA5"] = df["Close"] / df["MA5"]
df["precio_vs_MA10"] = df["Close"] / df["MA10"]
df["precio_vs_MA20"] = df["Close"] / df["MA20"]
df["precio_vs_MA50"] = df["Close"] / df["MA50"]

df["volatilidad_5d"] = df["return_1d"].rolling(5).std()
df["volatilidad_10d"] = df["return_1d"].rolling(10).std()
df["volatilidad_20d"] = df["return_1d"].rolling(20).std()

delta = df["Close"].diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss
df["RSI"] = 100 - (100 / (1 + rs))

ema12 = df["Close"].ewm(span=12).mean()
ema26 = df["Close"].ewm(span=26).mean()
df["MACD"] = ema12 - ema26
df["MACD_signal"] = df["MACD"].ewm(span=9).mean()
df["MACD_hist"] = df["MACD"] - df["MACD_signal"]

df["volumen_vs_media"] = df["Volume"] / df["Volume"].rolling(20).mean()
df["rango_diario"] = (df["High"] - df["Low"]) / df["Close"]
df["gap_apertura"] = (df["Open"] - df["Close"].shift(1)) / df["Close"].shift(1)

df["pos_rango_20d"] = (df["Close"] - df["Low"].rolling(20).min()) / \
                       (df["High"].rolling(20).max() - df["Low"].rolling(20).min())

df["dia_semana"] = df.index.dayofweek

# Target
df["target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)

print("   ✅ Features y target creados")


# ============================================================
# PARTE 2: PREPARAR DATOS (mismo split que Día 41)
# ============================================================

features = [
    "return_1d", "return_5d", "return_10d", "return_20d",
    "precio_vs_MA5", "precio_vs_MA10", "precio_vs_MA20", "precio_vs_MA50",
    "volatilidad_5d", "volatilidad_10d", "volatilidad_20d",
    "RSI", "MACD", "MACD_signal", "MACD_hist",
    "volumen_vs_media", "rango_diario", "gap_apertura",
    "pos_rango_20d", "dia_semana"
]

df_clean = df.dropna(subset=features + ["target"]).copy()

split_index = int(len(df_clean) * 0.8)
train = df_clean.iloc[:split_index]
test = df_clean.iloc[split_index:]

X_train = train[features]
y_train = train["target"]
X_test = test[features]
y_test = test["target"]

print(f"\n📦 Datos preparados:")
print(f"   📚 Train: {len(train)} filas ({train.index[0].strftime('%Y-%m-%d')} a {train.index[-1].strftime('%Y-%m-%d')})")
print(f"   🧪 Test:  {len(test)} filas ({test.index[0].strftime('%Y-%m-%d')} a {test.index[-1].strftime('%Y-%m-%d')})")

baseline = y_test.mean()
print(f"   📏 Baseline (siempre 'sube'): {baseline*100:.2f}%")


# ============================================================
# PARTE 3: ENTRENAR RANDOM FOREST (referencia del Día 41)
# ============================================================

print("\n" + "=" * 60)
print("  🌲 MODELO 1: RANDOM FOREST (referencia Día 41)")
print("=" * 60)

rf = RandomForestClassifier(
    n_estimators=200,
    max_depth=5,
    min_samples_split=20,
    min_samples_leaf=10,
    random_state=42,
    n_jobs=-1
)

rf.fit(X_train, y_train)

rf_pred_train = rf.predict(X_train)
rf_pred_test = rf.predict(X_test)

rf_acc_train = accuracy_score(y_train, rf_pred_train)
rf_acc_test = accuracy_score(y_test, rf_pred_test)
rf_prec = precision_score(y_test, rf_pred_test, zero_division=0)
rf_rec = recall_score(y_test, rf_pred_test, zero_division=0)
rf_f1 = f1_score(y_test, rf_pred_test, zero_division=0)

print(f"\n   Accuracy Train: {rf_acc_train:.4f} ({rf_acc_train*100:.2f}%)")
print(f"   Accuracy Test:  {rf_acc_test:.4f} ({rf_acc_test*100:.2f}%)")
print(f"   Overfitting:    {rf_acc_train - rf_acc_test:.4f}")
print(f"   Precision:      {rf_prec:.4f}")
print(f"   Recall:         {rf_rec:.4f}")
print(f"   F1 Score:       {rf_f1:.4f}")


# ============================================================
# PARTE 4: ENTRENAR XGBOOST — VERSIÓN BÁSICA
# ============================================================

print("\n" + "=" * 60)
print("  🚀 MODELO 2: XGBOOST (versión básica)")
print("=" * 60)

xgb_basic = XGBClassifier(
    n_estimators=200,
    max_depth=3,              # Menos profundo que RF → menos overfitting
    learning_rate=0.1,        # Velocidad de aprendizaje
    subsample=0.8,            # Usa 80% de datos por árbol (regularización)
    colsample_bytree=0.8,     # Usa 80% de features por árbol
    random_state=42,
    eval_metric="logloss",
    verbosity=0
)

xgb_basic.fit(X_train, y_train)

xgb1_pred_train = xgb_basic.predict(X_train)
xgb1_pred_test = xgb_basic.predict(X_test)

xgb1_acc_train = accuracy_score(y_train, xgb1_pred_train)
xgb1_acc_test = accuracy_score(y_test, xgb1_pred_test)
xgb1_prec = precision_score(y_test, xgb1_pred_test, zero_division=0)
xgb1_rec = recall_score(y_test, xgb1_pred_test, zero_division=0)
xgb1_f1 = f1_score(y_test, xgb1_pred_test, zero_division=0)

print(f"\n   Accuracy Train: {xgb1_acc_train:.4f} ({xgb1_acc_train*100:.2f}%)")
print(f"   Accuracy Test:  {xgb1_acc_test:.4f} ({xgb1_acc_test*100:.2f}%)")
print(f"   Overfitting:    {xgb1_acc_train - xgb1_acc_test:.4f}")
print(f"   Precision:      {xgb1_prec:.4f}")
print(f"   Recall:         {xgb1_rec:.4f}")
print(f"   F1 Score:       {xgb1_f1:.4f}")


# ============================================================
# PARTE 5: XGBOOST — VERSIÓN OPTIMIZADA (anti-overfitting)
# ============================================================

print("\n" + "=" * 60)
print("  🎯 MODELO 3: XGBOOST (optimizado anti-overfitting)")
print("=" * 60)

xgb_opt = XGBClassifier(
    n_estimators=100,          # Menos árboles
    max_depth=2,               # Muy poco profundo → generaliza mejor
    learning_rate=0.05,        # Aprende más lento → más estable
    subsample=0.7,             # Solo 70% de datos por árbol
    colsample_bytree=0.7,     # Solo 70% de features por árbol
    reg_alpha=1.0,             # Regularización L1 (penaliza complejidad)
    reg_lambda=2.0,            # Regularización L2 (penaliza complejidad)
    min_child_weight=10,       # Mínimo de muestras por hoja
    gamma=0.1,                 # Penalización por añadir más hojas
    random_state=42,
    eval_metric="logloss",
    verbosity=0
)

xgb_opt.fit(X_train, y_train)

xgb2_pred_train = xgb_opt.predict(X_train)
xgb2_pred_test = xgb_opt.predict(X_test)

xgb2_acc_train = accuracy_score(y_train, xgb2_pred_train)
xgb2_acc_test = accuracy_score(y_test, xgb2_pred_test)
xgb2_prec = precision_score(y_test, xgb2_pred_test, zero_division=0)
xgb2_rec = recall_score(y_test, xgb2_pred_test, zero_division=0)
xgb2_f1 = f1_score(y_test, xgb2_pred_test, zero_division=0)

print(f"\n   Accuracy Train: {xgb2_acc_train:.4f} ({xgb2_acc_train*100:.2f}%)")
print(f"   Accuracy Test:  {xgb2_acc_test:.4f} ({xgb2_acc_test*100:.2f}%)")
print(f"   Overfitting:    {xgb2_acc_train - xgb2_acc_test:.4f}")
print(f"   Precision:      {xgb2_prec:.4f}")
print(f"   Recall:         {xgb2_rec:.4f}")
print(f"   F1 Score:       {xgb2_f1:.4f}")


# ============================================================
# PARTE 6: FEATURES MÁS IMPORTANTES (XGBoost optimizado)
# ============================================================

print("\n🏆 TOP 10 FEATURES — XGBOOST OPTIMIZADO")
print("=" * 50)

importancias_xgb = pd.Series(
    xgb_opt.feature_importances_,
    index=features
).sort_values(ascending=False)

for i, (feat, imp) in enumerate(importancias_xgb.head(10).items()):
    barra = "█" * int(imp * 50)
    print(f"   {i+1:>2}. {feat:<20} {imp:.4f}  {barra}")


# ============================================================
# PARTE 7: COMPARACIÓN DIRECTA — TABLA RESUMEN
# ============================================================

print("\n" + "=" * 60)
print("  📊 COMPARACIÓN DIRECTA: 3 MODELOS")
print("=" * 60)

print(f"\n   {'Métrica':<22} {'RF':>10} {'XGB Básico':>12} {'XGB Optim.':>12}")
print(f"   {'------':<22} {'--':>10} {'----------':>12} {'----------':>12}")
print(f"   {'Accuracy Train':<22} {rf_acc_train:>10.4f} {xgb1_acc_train:>12.4f} {xgb2_acc_train:>12.4f}")
print(f"   {'Accuracy Test':<22} {rf_acc_test:>10.4f} {xgb1_acc_test:>12.4f} {xgb2_acc_test:>12.4f}")
print(f"   {'Overfitting':<22} {rf_acc_train-rf_acc_test:>10.4f} {xgb1_acc_train-xgb1_acc_test:>12.4f} {xgb2_acc_train-xgb2_acc_test:>12.4f}")
print(f"   {'Precision':<22} {rf_prec:>10.4f} {xgb1_prec:>12.4f} {xgb2_prec:>12.4f}")
print(f"   {'Recall':<22} {rf_rec:>10.4f} {xgb1_rec:>12.4f} {xgb2_rec:>12.4f}")
print(f"   {'F1 Score':<22} {rf_f1:>10.4f} {xgb1_f1:>12.4f} {xgb2_f1:>12.4f}")
print(f"   {'Baseline':<22} {baseline:>10.4f} {baseline:>12.4f} {baseline:>12.4f}")


# ============================================================
# PARTE 8: SIMULACIÓN DE TRADING — 3 MODELOS
# ============================================================

print("\n" + "=" * 60)
print("  💰 SIMULACIÓN DE TRADING — 3 MODELOS")
print("=" * 60)

sim = test.copy()

# Predicciones de cada modelo
sim["pred_rf"] = rf_pred_test
sim["pred_xgb1"] = xgb1_pred_test
sim["pred_xgb2"] = xgb2_pred_test

# Retorno del día siguiente
retorno_futuro = sim["return_1d"].shift(-1)

# Retorno de cada estrategia
sim["ret_rf"] = retorno_futuro * sim["pred_rf"]
sim["ret_xgb1"] = retorno_futuro * sim["pred_xgb1"]
sim["ret_xgb2"] = retorno_futuro * sim["pred_xgb2"]
sim["ret_bh"] = retorno_futuro

# Acumulados
sim["acum_rf"] = (1 + sim["ret_rf"]).cumprod()
sim["acum_xgb1"] = (1 + sim["ret_xgb1"]).cumprod()
sim["acum_xgb2"] = (1 + sim["ret_xgb2"]).cumprod()
sim["acum_bh"] = (1 + sim["ret_bh"]).cumprod()

# Resultados finales
ret_rf = (sim["acum_rf"].iloc[-2] - 1) * 100
ret_xgb1 = (sim["acum_xgb1"].iloc[-2] - 1) * 100
ret_xgb2 = (sim["acum_xgb2"].iloc[-2] - 1) * 100
ret_bh = (sim["acum_bh"].iloc[-2] - 1) * 100

print(f"\n   📊 Rendimiento en período de TEST:")
print(f"      🌲 Random Forest:    {ret_rf:>+8.2f}%")
print(f"      🚀 XGBoost Básico:   {ret_xgb1:>+8.2f}%")
print(f"      🎯 XGBoost Optimiz.: {ret_xgb2:>+8.2f}%")
print(f"      📈 Buy & Hold:       {ret_bh:>+8.2f}%")

# Sharpe Ratios
for nombre, col in [("RF", "ret_rf"), ("XGB Básico", "ret_xgb1"),
                     ("XGB Optim.", "ret_xgb2"), ("B&H", "ret_bh")]:
    rets = sim[col].dropna()
    if rets.std() > 0:
        sharpe = (rets.mean() / rets.std()) * np.sqrt(252)
        print(f"      📐 Sharpe {nombre:<12}: {sharpe:.4f}")

# Días invertido por modelo
print(f"\n   📅 Días invertido:")
print(f"      🌲 RF:         {sim['pred_rf'].sum():.0f} de {len(sim)} ({sim['pred_rf'].mean()*100:.1f}%)")
print(f"      🚀 XGB Básico: {sim['pred_xgb1'].sum():.0f} de {len(sim)} ({sim['pred_xgb1'].mean()*100:.1f}%)")
print(f"      🎯 XGB Optim.: {sim['pred_xgb2'].sum():.0f} de {len(sim)} ({sim['pred_xgb2'].mean()*100:.1f}%)")

# Mejor modelo
resultados = {
    "Random Forest": ret_rf,
    "XGBoost Básico": ret_xgb1,
    "XGBoost Optimizado": ret_xgb2
}
mejor = max(resultados, key=resultados.get)
print(f"\n   🏆 Mejor modelo por retorno: {mejor} ({resultados[mejor]:+.2f}%)")


# ============================================================
# PARTE 9: PREDICCIÓN PARA MAÑANA — TODOS LOS MODELOS
# ============================================================

print("\n" + "=" * 60)
print("  🔮 PREDICCIÓN PARA EL PRÓXIMO DÍA — 3 MODELOS")
print("=" * 60)

ultimo_dia = df_clean[features].iloc[-1:]
fecha_ultimo = df_clean.index[-1].strftime("%Y-%m-%d")

print(f"\n   📅 Basado en datos del: {fecha_ultimo}\n")

modelos = [
    ("🌲 Random Forest", rf),
    ("🚀 XGBoost Básico", xgb_basic),
    ("🎯 XGBoost Optimizado", xgb_opt)
]

votos_sube = 0
votos_baja = 0

for nombre, modelo in modelos:
    pred = modelo.predict(ultimo_dia)[0]
    prob = modelo.predict_proba(ultimo_dia)[0]
    conf = max(prob)
    direccion = "SUBE" if pred == 1 else "BAJA"
    emoji = "📈" if pred == 1 else "📉"

    if pred == 1:
        votos_sube += 1
    else:
        votos_baja += 1

    print(f"   {nombre}:")
    print(f"      Predicción: {emoji} {direccion} (confianza: {conf*100:.1f}%)")
    print(f"      Prob. subir: {prob[1]*100:.1f}% | Prob. bajar: {prob[0]*100:.1f}%")
    print()

# Consenso
print(f"   📊 CONSENSO DE MODELOS:")
print(f"      Votos SUBE: {votos_sube}")
print(f"      Votos BAJA: {votos_baja}")

if votos_sube > votos_baja:
    print(f"      ✅ Señal CONSENSO: COMPRAR (mayoría predice subida)")
elif votos_baja > votos_sube:
    print(f"      🔴 Señal CONSENSO: NO COMPRAR (mayoría predice bajada)")
else:
    print(f"      ⏸️ Señal CONSENSO: EMPATE — mejor esperar")


# ============================================================
# PARTE 10: RESUMEN
# ============================================================

print("\n" + "=" * 60)
print("  ✅ DÍA 42 COMPLETADO")
print("=" * 60)
