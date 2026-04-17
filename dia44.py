"""
DÍA 44: Backtesting ML vs Estrategias Tradicionales
====================================================
Bootcamp Quant Trading - Irene Tanarro

Comparación rigurosa:
- XGBoost (mejor ML) con walk-forward
- Trend Following MA20/MA50 (mejor tradicional)
- Buy & Hold (benchmark)

Walk-forward: entrenar con 2 años, predecir 1 mes, avanzar, repetir.

Requisitos: pip install xgboost scikit-learn yfinance pandas numpy
"""

import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier
import warnings
warnings.filterwarnings("ignore")


# ============================================================
# PARTE 1: DATOS Y FEATURES
# ============================================================

print("=" * 60)
print("  📊 DÍA 44: ML vs TREND FOLLOWING vs BUY & HOLD")
print("  🔄 Backtesting con Walk-Forward")
print("=" * 60)

print("\n📥 Descargando datos de AAPL...")

ticker = "AAPL"
data = yf.download(ticker, start="2019-01-01", end="2025-12-31", progress=False)

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

print(f"   ✅ {len(data)} días descargados")

df = data.copy()

# Features
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

# Señal Trend Following MA20/MA50
df["signal_tf"] = 0
df.loc[df["MA20"] > df["MA50"], "signal_tf"] = 1   # Comprar cuando MA20 > MA50
df.loc[df["MA20"] <= df["MA50"], "signal_tf"] = 0   # Vender cuando MA20 <= MA50

features = [
    "return_1d", "return_5d", "return_10d", "return_20d",
    "precio_vs_MA5", "precio_vs_MA10", "precio_vs_MA20", "precio_vs_MA50",
    "volatilidad_5d", "volatilidad_10d", "volatilidad_20d",
    "RSI", "MACD", "MACD_signal", "MACD_hist",
    "volumen_vs_media", "rango_diario", "gap_apertura",
    "pos_rango_20d", "dia_semana"
]

df_clean = df.dropna(subset=features + ["target"]).copy()
print(f"   ✅ {len(df_clean)} filas listas")


# ============================================================
# PARTE 2: WALK-FORWARD TESTING
# ============================================================
# Entrenamos con 500 días, predecimos los siguientes 21 días (1 mes),
# luego avanzamos 21 días y repetimos.
# Esto simula la realidad: reentrenar periódicamente.

print("\n🔄 WALK-FORWARD TESTING")
print("=" * 50)

TRAIN_SIZE = 500    # Días de entrenamiento
STEP_SIZE = 21      # Avanzar 21 días (~1 mes) entre reentrenamientos

resultados_wf = []  # Guardará predicciones y señales

inicio_test = TRAIN_SIZE
total_ventanas = 0

print(f"   📐 Ventana de entrenamiento: {TRAIN_SIZE} días")
print(f"   📐 Paso de avance: {STEP_SIZE} días")
print(f"   📐 Datos totales: {len(df_clean)} días")
print(f"\n   ⏳ Ejecutando walk-forward...\n")

i = inicio_test
while i < len(df_clean) - 1:
    fin_test = min(i + STEP_SIZE, len(df_clean) - 1)

    # Datos de entrenamiento (últimos TRAIN_SIZE días antes del test)
    train_data = df_clean.iloc[max(0, i - TRAIN_SIZE):i]
    test_data = df_clean.iloc[i:fin_test]

    if len(test_data) == 0:
        break

    X_train = train_data[features]
    y_train = train_data["target"]
    X_test = test_data[features]

    # Entrenar XGBoost
    modelo = XGBClassifier(
        n_estimators=100, max_depth=2, learning_rate=0.05,
        subsample=0.7, colsample_bytree=0.7, reg_alpha=1.0,
        reg_lambda=2.0, min_child_weight=10, gamma=0.1,
        random_state=42, eval_metric="logloss", verbosity=0
    )
    modelo.fit(X_train, y_train)

    # Predecir
    predicciones = modelo.predict(X_test)

    # Guardar resultados
    for j, idx in enumerate(test_data.index):
        resultados_wf.append({
            "fecha": idx,
            "close": df_clean.loc[idx, "Close"],
            "return_1d": df_clean.loc[idx, "return_1d"],
            "target": df_clean.loc[idx, "target"],
            "pred_ml": predicciones[j],
            "signal_tf": df_clean.loc[idx, "signal_tf"]
        })

    total_ventanas += 1
    periodo_train = f"{train_data.index[0].strftime('%Y-%m')}"
    periodo_test = f"{test_data.index[0].strftime('%Y-%m-%d')} a {test_data.index[-1].strftime('%Y-%m-%d')}"
    acc_ventana = accuracy_score(test_data["target"], predicciones)
    print(f"   Ventana {total_ventanas:>3}: Train desde {periodo_train} | Test: {periodo_test} | Acc: {acc_ventana:.2%}")

    i += STEP_SIZE

print(f"\n   ✅ Walk-forward completado: {total_ventanas} ventanas")


# ============================================================
# PARTE 3: CALCULAR RESULTADOS
# ============================================================

print("\n📊 CALCULANDO RESULTADOS...")

res = pd.DataFrame(resultados_wf)
res.set_index("fecha", inplace=True)

# Retorno del día siguiente
res["retorno_futuro"] = res["return_1d"].shift(-1)

# Retorno de cada estrategia
res["ret_ml"] = res["retorno_futuro"] * res["pred_ml"]
res["ret_tf"] = res["retorno_futuro"] * res["signal_tf"]
res["ret_bh"] = res["retorno_futuro"]

# Acumulados
res["acum_ml"] = (1 + res["ret_ml"]).cumprod()
res["acum_tf"] = (1 + res["ret_tf"]).cumprod()
res["acum_bh"] = (1 + res["ret_bh"]).cumprod()


# ============================================================
# PARTE 4: MÉTRICAS COMPLETAS
# ============================================================

print("\n" + "=" * 60)
print("  📊 RESULTADOS: ML vs TREND FOLLOWING vs BUY & HOLD")
print("=" * 60)

# Período de test
print(f"\n   📅 Período: {res.index[0].strftime('%Y-%m-%d')} a {res.index[-1].strftime('%Y-%m-%d')}")
print(f"   📅 Total: {len(res)} días de trading")

# --- Retorno total ---
ret_ml = (res["acum_ml"].iloc[-2] - 1) * 100
ret_tf = (res["acum_tf"].iloc[-2] - 1) * 100
ret_bh = (res["acum_bh"].iloc[-2] - 1) * 100

# --- Sharpe Ratio ---
def calc_sharpe(returns):
    r = returns.dropna()
    if r.std() == 0:
        return 0
    return (r.mean() / r.std()) * np.sqrt(252)

sharpe_ml = calc_sharpe(res["ret_ml"])
sharpe_tf = calc_sharpe(res["ret_tf"])
sharpe_bh = calc_sharpe(res["ret_bh"])

# --- Maximum Drawdown ---
def calc_max_drawdown(acum):
    peak = acum.cummax()
    drawdown = (acum - peak) / peak
    return drawdown.min() * 100

mdd_ml = calc_max_drawdown(res["acum_ml"])
mdd_tf = calc_max_drawdown(res["acum_tf"])
mdd_bh = calc_max_drawdown(res["acum_bh"])

# --- Accuracy ML ---
acc_ml = accuracy_score(res["target"], res["pred_ml"])

# --- Win Rate (días con retorno positivo) ---
def calc_win_rate(returns, signals):
    trading_days = returns[signals == 1].dropna()
    if len(trading_days) == 0:
        return 0
    return (trading_days > 0).mean() * 100

wr_ml = calc_win_rate(res["retorno_futuro"], res["pred_ml"])
wr_tf = calc_win_rate(res["retorno_futuro"], res["signal_tf"])
wr_bh = calc_win_rate(res["retorno_futuro"], pd.Series(1, index=res.index))

# --- Días invertido ---
dias_ml = res["pred_ml"].sum()
dias_tf = res["signal_tf"].sum()
dias_total = len(res)

# --- Tabla comparativa ---
print(f"\n   {'Métrica':<25} {'XGBoost ML':>12} {'Trend Follow':>12} {'Buy & Hold':>12}")
print(f"   {'-'*25} {'-'*12} {'-'*12} {'-'*12}")
print(f"   {'Retorno Total':<25} {ret_ml:>+11.2f}% {ret_tf:>+11.2f}% {ret_bh:>+11.2f}%")
print(f"   {'Sharpe Ratio':<25} {sharpe_ml:>12.4f} {sharpe_tf:>12.4f} {sharpe_bh:>12.4f}")
print(f"   {'Max Drawdown':<25} {mdd_ml:>11.2f}% {mdd_tf:>11.2f}% {mdd_bh:>11.2f}%")
print(f"   {'Win Rate':<25} {wr_ml:>11.2f}% {wr_tf:>11.2f}% {wr_bh:>11.2f}%")
print(f"   {'Días invertido':<25} {dias_ml:>8.0f}/{dias_total:<3} {dias_tf:>8.0f}/{dias_total:<3} {dias_total:>8}/{dias_total:<3}")
print(f"   {'% tiempo en mercado':<25} {dias_ml/dias_total*100:>11.1f}% {dias_tf/dias_total*100:>11.1f}% {'100.0':>11}%")

# Accuracy solo aplica a ML
print(f"\n   🎯 Accuracy ML (walk-forward): {acc_ml:.4f} ({acc_ml*100:.2f}%)")
print(f"   📏 Baseline (siempre 'sube'):   {res['target'].mean():.4f} ({res['target'].mean()*100:.2f}%)")


# ============================================================
# PARTE 5: ANÁLISIS POR AÑO
# ============================================================

print("\n" + "=" * 60)
print("  📅 RENDIMIENTO POR AÑO")
print("=" * 60)

res["year"] = res.index.year

print(f"\n   {'Año':<8} {'XGBoost ML':>12} {'Trend Follow':>12} {'Buy & Hold':>12}")
print(f"   {'-'*8} {'-'*12} {'-'*12} {'-'*12}")

for year in sorted(res["year"].unique()):
    year_data = res[res["year"] == year]

    acum_ml_y = (1 + year_data["ret_ml"]).cumprod()
    acum_tf_y = (1 + year_data["ret_tf"]).cumprod()
    acum_bh_y = (1 + year_data["ret_bh"]).cumprod()

    r_ml = (acum_ml_y.iloc[-1] - 1) * 100 if len(acum_ml_y) > 0 else 0
    r_tf = (acum_tf_y.iloc[-1] - 1) * 100 if len(acum_tf_y) > 0 else 0
    r_bh = (acum_bh_y.iloc[-1] - 1) * 100 if len(acum_bh_y) > 0 else 0

    # Marcar el ganador de cada año
    mejor = max(r_ml, r_tf, r_bh)
    mark_ml = " 🏆" if r_ml == mejor else ""
    mark_tf = " 🏆" if r_tf == mejor else ""
    mark_bh = " 🏆" if r_bh == mejor else ""

    print(f"   {year:<8} {r_ml:>+10.2f}%{mark_ml} {r_tf:>+10.2f}%{mark_tf} {r_bh:>+10.2f}%{mark_bh}")


# ============================================================
# PARTE 6: DECISIÓN PARA EL BOT
# ============================================================

print("\n" + "=" * 60)
print("  🤖 DECISIÓN PARA TU BOT DE TRADING")
print("=" * 60)

print(f"""
   Basado en los resultados del walk-forward testing:

   📊 RETORNO: """)

# Ordenar por retorno
ranking_ret = sorted([
    ("XGBoost ML", ret_ml),
    ("Trend Following", ret_tf),
    ("Buy & Hold", ret_bh)
], key=lambda x: x[1], reverse=True)

for i, (nombre, ret) in enumerate(ranking_ret):
    medal = ["🥇", "🥈", "🥉"][i]
    print(f"      {medal} {nombre}: {ret:+.2f}%")

print(f"\n   📐 SHARPE (retorno ajustado al riesgo):")

ranking_sharpe = sorted([
    ("XGBoost ML", sharpe_ml),
    ("Trend Following", sharpe_tf),
    ("Buy & Hold", sharpe_bh)
], key=lambda x: x[1], reverse=True)

for i, (nombre, s) in enumerate(ranking_sharpe):
    medal = ["🥇", "🥈", "🥉"][i]
    print(f"      {medal} {nombre}: {s:.4f}")

print(f"\n   📉 DRAWDOWN (menor pérdida máxima = mejor):")

ranking_mdd = sorted([
    ("XGBoost ML", mdd_ml),
    ("Trend Following", mdd_tf),
    ("Buy & Hold", mdd_bh)
], key=lambda x: x[1], reverse=True)  # Menos negativo = mejor

for i, (nombre, d) in enumerate(ranking_mdd):
    medal = ["🥇", "🥈", "🥉"][i]
    print(f"      {medal} {nombre}: {d:.2f}%")

# Recomendación
print(f"""
   💡 RECOMENDACIÓN:

   Para tu bot v2, la mejor opción es usar un ENSEMBLE
   (combinación) de modelos:

   1. Señal PRIMARIA: Trend Following MA20/MA50
      → Es simple, robusto y tiene track record largo

   2. Filtro ML: XGBoost como confirmación
      → Solo operar cuando Trend Following Y XGBoost coincidan
      → Esto reduce operaciones pero mejora la calidad

   3. Benchmark: Buy & Hold
      → Si tu bot no supera B&H en 3 meses, simplemente holdear

   Esta combinación (TF + ML) es lo que hacen muchos fondos:
   estrategia simple + filtro inteligente.
""")


# ============================================================
# PARTE 7: SIMULAR ENSEMBLE (TF + ML)
# ============================================================

print("=" * 60)
print("  🔗 BONUS: ENSEMBLE (Trend Following + ML)")
print("=" * 60)

# Solo comprar cuando AMBOS dicen "compra"
res["signal_ensemble"] = ((res["pred_ml"] == 1) & (res["signal_tf"] == 1)).astype(int)
res["ret_ensemble"] = res["retorno_futuro"] * res["signal_ensemble"]
res["acum_ensemble"] = (1 + res["ret_ensemble"]).cumprod()

ret_ensemble = (res["acum_ensemble"].iloc[-2] - 1) * 100
sharpe_ensemble = calc_sharpe(res["ret_ensemble"])
mdd_ensemble = calc_max_drawdown(res["acum_ensemble"])
wr_ensemble = calc_win_rate(res["retorno_futuro"], res["signal_ensemble"])
dias_ensemble = res["signal_ensemble"].sum()

print(f"\n   📊 Ensemble (TF + ML combinado):")
print(f"      Retorno:      {ret_ensemble:>+8.2f}%")
print(f"      Sharpe:       {sharpe_ensemble:>8.4f}")
print(f"      Max Drawdown: {mdd_ensemble:>7.2f}%")
print(f"      Win Rate:     {wr_ensemble:>7.2f}%")
print(f"      Días operado: {dias_ensemble:.0f} de {dias_total} ({dias_ensemble/dias_total*100:.1f}%)")

print(f"\n   📊 COMPARACIÓN FINAL:")
print(f"\n   {'Estrategia':<22} {'Retorno':>10} {'Sharpe':>10} {'Drawdown':>10}")
print(f"   {'-'*22} {'-'*10} {'-'*10} {'-'*10}")
print(f"   {'XGBoost ML':<22} {ret_ml:>+9.2f}% {sharpe_ml:>10.4f} {mdd_ml:>9.2f}%")
print(f"   {'Trend Following':<22} {ret_tf:>+9.2f}% {sharpe_tf:>10.4f} {mdd_tf:>9.2f}%")
print(f"   {'ENSEMBLE (TF+ML)':<22} {ret_ensemble:>+9.2f}% {sharpe_ensemble:>10.4f} {mdd_ensemble:>9.2f}%")
print(f"   {'Buy & Hold':<22} {ret_bh:>+9.2f}% {sharpe_bh:>10.4f} {mdd_bh:>9.2f}%")


# ============================================================
# PARTE 8: RESUMEN
# ============================================================

print("\n" + "=" * 60)
print("  ✅ DÍA 44 COMPLETADO")
print("=" * 60)
