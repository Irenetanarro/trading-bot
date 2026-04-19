"""
DÍA 45: Feature Engineering Avanzado
=====================================
Bootcamp Quant Trading - Irene Tanarro

Objetivo: Mejorar el modelo XGBoost añadiendo features profesionales.
Comparar: XGBoost con 20 features básicas vs XGBoost con 40+ features avanzadas.
Método: Walk-forward testing (mismo que Día 44) para comparación justa.

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
# PARTE 1: DESCARGAR DATOS
# ============================================================

print("=" * 60)
print("  🔬 DÍA 45: FEATURE ENGINEERING AVANZADO")
print("  📊 Features básicas vs Features profesionales")
print("=" * 60)

print("\n📥 Descargando datos de AAPL...")

ticker = "AAPL"
data = yf.download(ticker, start="2019-01-01", end="2025-12-31", progress=False)

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

print(f"   ✅ {len(data)} días descargados")

df = data.copy()


# ============================================================
# PARTE 2: FEATURES BÁSICAS (las de los Días 41-44)
# ============================================================

print("\n🔧 Creando features BÁSICAS (20 features)...")

# Retornos
df["return_1d"] = df["Close"].pct_change(1)
df["return_5d"] = df["Close"].pct_change(5)
df["return_10d"] = df["Close"].pct_change(10)
df["return_20d"] = df["Close"].pct_change(20)

# Medias Móviles
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

# Otras
df["volumen_vs_media"] = df["Volume"] / df["Volume"].rolling(20).mean()
df["rango_diario"] = (df["High"] - df["Low"]) / df["Close"]
df["gap_apertura"] = (df["Open"] - df["Close"].shift(1)) / df["Close"].shift(1)
df["pos_rango_20d"] = (df["Close"] - df["Low"].rolling(20).min()) / \
                       (df["High"].rolling(20).max() - df["Low"].rolling(20).min())
df["dia_semana"] = df.index.dayofweek

features_basicas = [
    "return_1d", "return_5d", "return_10d", "return_20d",
    "precio_vs_MA5", "precio_vs_MA10", "precio_vs_MA20", "precio_vs_MA50",
    "volatilidad_5d", "volatilidad_10d", "volatilidad_20d",
    "RSI", "MACD", "MACD_signal", "MACD_hist",
    "volumen_vs_media", "rango_diario", "gap_apertura",
    "pos_rango_20d", "dia_semana"
]

print(f"   ✅ {len(features_basicas)} features básicas")


# ============================================================
# PARTE 3: FEATURES AVANZADAS (nuevas)
# ============================================================

print("\n🔬 Creando features AVANZADAS (20+ features nuevas)...\n")

# --- GRUPO 1: PATRONES DE VELAS (Candlestick) ---
print("   📊 Grupo 1: Patrones de velas...")

# Tamaño del cuerpo de la vela (diferencia open-close relativa)
df["cuerpo_vela"] = (df["Close"] - df["Open"]) / df["Open"]

# Sombra superior (mecha arriba)
df["sombra_superior"] = (df["High"] - df[["Open", "Close"]].max(axis=1)) / df["Close"]

# Sombra inferior (mecha abajo)
df["sombra_inferior"] = (df[["Open", "Close"]].min(axis=1) - df["Low"]) / df["Close"]

# Ratio cuerpo vs rango total (velas con mucho cuerpo = tendencia fuerte)
rango = df["High"] - df["Low"]
cuerpo = abs(df["Close"] - df["Open"])
df["ratio_cuerpo_rango"] = cuerpo / rango.replace(0, np.nan)

# Velas consecutivas del mismo color
df["vela_positiva"] = (df["Close"] > df["Open"]).astype(int)
df["rachas_positivas"] = df["vela_positiva"].rolling(5).sum()  # Cuántas de las últimas 5 son verdes


# --- GRUPO 2: FEATURES ESTADÍSTICAS AVANZADAS ---
print("   📐 Grupo 2: Features estadísticas...")

# Skewness (asimetría de retornos) — si es negativa, hay más caídas fuertes
df["skew_10d"] = df["return_1d"].rolling(10).skew()
df["skew_20d"] = df["return_1d"].rolling(20).skew()

# Kurtosis (colas pesadas) — alta kurtosis = movimientos extremos más frecuentes
df["kurt_10d"] = df["return_1d"].rolling(10).kurt()
df["kurt_20d"] = df["return_1d"].rolling(20).kurt()

# Z-score del precio (cuántas desviaciones estándar está del precio medio)
df["zscore_20d"] = (df["Close"] - df["Close"].rolling(20).mean()) / df["Close"].rolling(20).std()
df["zscore_50d"] = (df["Close"] - df["Close"].rolling(50).mean()) / df["Close"].rolling(50).std()


# --- GRUPO 3: FEATURES DE VOLUMEN AVANZADAS ---
print("   📊 Grupo 3: Features de volumen...")

# OBV simplificado (On-Balance Volume) — acumulado de volumen según dirección
df["obv_change"] = np.where(df["Close"] > df["Close"].shift(1),
                             df["Volume"],
                             np.where(df["Close"] < df["Close"].shift(1),
                                      -df["Volume"], 0))
df["obv_5d"] = df["obv_change"].rolling(5).sum()
df["obv_ratio"] = df["obv_5d"] / (df["Volume"].rolling(5).sum() + 1)

# Volumen en días de subida vs bajada
df["vol_up"] = df["Volume"].where(df["return_1d"] > 0, 0).rolling(10).mean()
df["vol_down"] = df["Volume"].where(df["return_1d"] <= 0, 0).rolling(10).mean()
df["vol_up_down_ratio"] = df["vol_up"] / (df["vol_down"] + 1)


# --- GRUPO 4: FEATURES DE RÉGIMEN DE MERCADO ---
print("   🌍 Grupo 4: Features de régimen de mercado...")

# Volatilidad actual vs histórica (régimen de alta/baja vol)
df["vol_ratio_5_20"] = df["volatilidad_5d"] / (df["volatilidad_20d"] + 0.0001)

# Tendencia de la volatilidad (¿está subiendo o bajando?)
df["vol_trend"] = df["volatilidad_5d"] - df["volatilidad_20d"]

# Ratio de nuevos máximos vs mínimos en 20 días
df["pct_desde_max_20d"] = (df["Close"] - df["High"].rolling(20).max()) / df["High"].rolling(20).max()
df["pct_desde_min_20d"] = (df["Close"] - df["Low"].rolling(20).min()) / df["Low"].rolling(20).min()

# MA200 (tendencia de largo plazo)
df["MA200"] = df["Close"].rolling(200).mean()
df["precio_vs_MA200"] = df["Close"] / df["MA200"]

# Cruce de medias como feature numérica
df["ma_spread_20_50"] = (df["MA20"] - df["MA50"]) / df["MA50"]


# --- GRUPO 5: FEATURES TEMPORALES AVANZADAS ---
print("   📅 Grupo 5: Features temporales...")

# Mes del año (efecto enero, efecto septiembre, etc.)
df["mes"] = df.index.month

# ¿Estamos en primera o segunda mitad del mes?
df["mitad_mes"] = (df.index.day > 15).astype(int)

# Retorno del mismo día de la semana anterior
df["return_mismo_dia_sem"] = df["Close"] / df["Close"].shift(5) - 1


# Lista completa de features avanzadas
features_avanzadas = features_basicas + [
    # Patrones de velas
    "cuerpo_vela", "sombra_superior", "sombra_inferior",
    "ratio_cuerpo_rango", "rachas_positivas",
    # Estadísticas
    "skew_10d", "skew_20d", "kurt_10d", "kurt_20d",
    "zscore_20d", "zscore_50d",
    # Volumen
    "obv_ratio", "vol_up_down_ratio",
    # Régimen
    "vol_ratio_5_20", "vol_trend",
    "pct_desde_max_20d", "pct_desde_min_20d",
    "precio_vs_MA200", "ma_spread_20_50",
    # Temporales
    "mes", "mitad_mes", "return_mismo_dia_sem"
]

print(f"\n   ✅ {len(features_avanzadas)} features totales ({len(features_avanzadas) - len(features_basicas)} nuevas)")

# Target
df["target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)

# Limpiar NaN
df_basic = df.dropna(subset=features_basicas + ["target"]).copy()
df_advanced = df.dropna(subset=features_avanzadas + ["target"]).copy()

print(f"   📊 Datos con features básicas:   {len(df_basic)} filas")
print(f"   📊 Datos con features avanzadas: {len(df_advanced)} filas")


# ============================================================
# PARTE 4: WALK-FORWARD — FEATURES BÁSICAS
# ============================================================

print("\n" + "=" * 60)
print("  🔄 WALK-FORWARD: FEATURES BÁSICAS (20 features)")
print("=" * 60)

TRAIN_SIZE = 500
STEP_SIZE = 21

def walk_forward(datos, features_list, nombre):
    """Ejecuta walk-forward testing y devuelve resultados."""
    resultados = []
    i = TRAIN_SIZE

    while i < len(datos) - 1:
        fin_test = min(i + STEP_SIZE, len(datos) - 1)

        train_data = datos.iloc[max(0, i - TRAIN_SIZE):i]
        test_data = datos.iloc[i:fin_test]

        if len(test_data) == 0:
            break

        X_train = train_data[features_list]
        y_train = train_data["target"]
        X_test = test_data[features_list]

        modelo = XGBClassifier(
            n_estimators=100, max_depth=2, learning_rate=0.05,
            subsample=0.7, colsample_bytree=0.7, reg_alpha=1.0,
            reg_lambda=2.0, min_child_weight=10, gamma=0.1,
            random_state=42, eval_metric="logloss", verbosity=0
        )
        modelo.fit(X_train, y_train)

        predicciones = modelo.predict(X_test)

        for j, idx in enumerate(test_data.index):
            resultados.append({
                "fecha": idx,
                "return_1d": datos.loc[idx, "return_1d"],
                "target": datos.loc[idx, "target"],
                "pred": predicciones[j]
            })

        i += STEP_SIZE

    res = pd.DataFrame(resultados).set_index("fecha")
    return res

print("\n   ⏳ Ejecutando walk-forward con features básicas...")
res_basic = walk_forward(df_basic, features_basicas, "Básicas")
print(f"   ✅ Completado: {len(res_basic)} predicciones")


# ============================================================
# PARTE 5: WALK-FORWARD — FEATURES AVANZADAS
# ============================================================

print("\n" + "=" * 60)
print("  🔄 WALK-FORWARD: FEATURES AVANZADAS (42 features)")
print("=" * 60)

print("\n   ⏳ Ejecutando walk-forward con features avanzadas...")
res_adv = walk_forward(df_advanced, features_avanzadas, "Avanzadas")
print(f"   ✅ Completado: {len(res_adv)} predicciones")


# ============================================================
# PARTE 6: CALCULAR MÉTRICAS
# ============================================================

def calcular_metricas(res, nombre):
    """Calcula todas las métricas para un conjunto de resultados."""
    res = res.copy()
    res["retorno_futuro"] = res["return_1d"].shift(-1)
    res["ret_modelo"] = res["retorno_futuro"] * res["pred"]
    res["ret_bh"] = res["retorno_futuro"]

    res["acum_modelo"] = (1 + res["ret_modelo"]).cumprod()
    res["acum_bh"] = (1 + res["ret_bh"]).cumprod()

    retorno = (res["acum_modelo"].iloc[-2] - 1) * 100
    retorno_bh = (res["acum_bh"].iloc[-2] - 1) * 100

    rets = res["ret_modelo"].dropna()
    sharpe = (rets.mean() / rets.std()) * np.sqrt(252) if rets.std() > 0 else 0

    peak = res["acum_modelo"].cummax()
    mdd = ((res["acum_modelo"] - peak) / peak).min() * 100

    acc = accuracy_score(res["target"], res["pred"])

    trading_days = res["retorno_futuro"][res["pred"] == 1].dropna()
    win_rate = (trading_days > 0).mean() * 100 if len(trading_days) > 0 else 0

    dias_inv = res["pred"].sum()
    total = len(res)

    return {
        "nombre": nombre,
        "retorno": retorno,
        "retorno_bh": retorno_bh,
        "sharpe": sharpe,
        "mdd": mdd,
        "accuracy": acc,
        "win_rate": win_rate,
        "dias_inv": dias_inv,
        "total": total,
        "pct_mercado": dias_inv / total * 100
    }


m_basic = calcular_metricas(res_basic, "XGB Básico (20 feat.)")
m_adv = calcular_metricas(res_adv, "XGB Avanzado (42 feat.)")


# ============================================================
# PARTE 7: COMPARACIÓN
# ============================================================

print("\n" + "=" * 60)
print("  📊 COMPARACIÓN: FEATURES BÁSICAS vs AVANZADAS")
print("=" * 60)

print(f"\n   {'Métrica':<25} {'Básicas (20)':>14} {'Avanzadas (42)':>16}")
print(f"   {'-'*25} {'-'*14} {'-'*16}")
print(f"   {'Retorno Total':<25} {m_basic['retorno']:>+13.2f}% {m_adv['retorno']:>+15.2f}%")
print(f"   {'Sharpe Ratio':<25} {m_basic['sharpe']:>14.4f} {m_adv['sharpe']:>16.4f}")
print(f"   {'Max Drawdown':<25} {m_basic['mdd']:>13.2f}% {m_adv['mdd']:>15.2f}%")
print(f"   {'Accuracy':<25} {m_basic['accuracy']:>13.2%} {m_adv['accuracy']:>15.2%}")
print(f"   {'Win Rate':<25} {m_basic['win_rate']:>13.2f}% {m_adv['win_rate']:>15.2f}%")
print(f"   {'Días invertido':<25} {m_basic['dias_inv']:>9.0f}/{m_basic['total']:<4} {m_adv['dias_inv']:>11.0f}/{m_adv['total']:<4}")
print(f"   {'% en mercado':<25} {m_basic['pct_mercado']:>13.1f}% {m_adv['pct_mercado']:>15.1f}%")

print(f"\n   📈 Buy & Hold (referencia): +{m_basic['retorno_bh']:.2f}%")

# Análisis de mejora
print(f"\n   📐 ANÁLISIS DE MEJORA:")
diff_ret = m_adv["retorno"] - m_basic["retorno"]
diff_sharpe = m_adv["sharpe"] - m_basic["sharpe"]
diff_mdd = m_adv["mdd"] - m_basic["mdd"]
diff_acc = m_adv["accuracy"] - m_basic["accuracy"]

print(f"      Retorno:  {diff_ret:>+.2f} pp {'✅ Mejora' if diff_ret > 0 else '❌ Empeora'}")
print(f"      Sharpe:   {diff_sharpe:>+.4f} {'✅ Mejora' if diff_sharpe > 0 else '❌ Empeora'}")
print(f"      Drawdown: {diff_mdd:>+.2f} pp {'✅ Mejora' if diff_mdd > 0 else '❌ Empeora'}")
print(f"      Accuracy: {diff_acc:>+.4f} {'✅ Mejora' if diff_acc > 0 else '❌ Empeora'}")


# ============================================================
# PARTE 8: FEATURES MÁS IMPORTANTES (modelo avanzado)
# ============================================================

print("\n" + "=" * 60)
print("  🏆 TOP 15 FEATURES — MODELO AVANZADO")
print("=" * 60)

# Entrenar modelo final con todos los datos para ver importancias
modelo_final = XGBClassifier(
    n_estimators=100, max_depth=2, learning_rate=0.05,
    subsample=0.7, colsample_bytree=0.7, reg_alpha=1.0,
    reg_lambda=2.0, min_child_weight=10, gamma=0.1,
    random_state=42, eval_metric="logloss", verbosity=0
)
modelo_final.fit(df_advanced[features_avanzadas], df_advanced["target"])

importancias = pd.Series(
    modelo_final.feature_importances_,
    index=features_avanzadas
).sort_values(ascending=False)

print(f"\n   {'#':<4} {'Feature':<25} {'Importancia':>12} {'Tipo':>12}")
print(f"   {'-'*4} {'-'*25} {'-'*12} {'-'*12}")

tipo_feature = {}
for f in features_basicas:
    tipo_feature[f] = "Básica"
for f in features_avanzadas:
    if f not in tipo_feature:
        tipo_feature[f] = "⭐ NUEVA"

for i, (feat, imp) in enumerate(importancias.head(15).items()):
    barra = "█" * int(imp * 80)
    tipo = tipo_feature.get(feat, "?")
    print(f"   {i+1:>3}. {feat:<25} {imp:>10.4f}   {tipo:<10} {barra}")

# Contar nuevas features en top 15
nuevas_en_top = sum(1 for f in importancias.head(15).index if tipo_feature.get(f) == "⭐ NUEVA")
print(f"\n   📊 Features NUEVAS en Top 15: {nuevas_en_top} de 15")
print(f"   📊 Features BÁSICAS en Top 15: {15 - nuevas_en_top} de 15")


# ============================================================
# PARTE 9: RENDIMIENTO POR AÑO
# ============================================================

print("\n" + "=" * 60)
print("  📅 RENDIMIENTO POR AÑO")
print("=" * 60)

# Preparar datos por año
res_basic_copy = res_basic.copy()
res_adv_copy = res_adv.copy()

res_basic_copy["retorno_futuro"] = res_basic_copy["return_1d"].shift(-1)
res_basic_copy["ret"] = res_basic_copy["retorno_futuro"] * res_basic_copy["pred"]
res_basic_copy["year"] = res_basic_copy.index.year

res_adv_copy["retorno_futuro"] = res_adv_copy["return_1d"].shift(-1)
res_adv_copy["ret"] = res_adv_copy["retorno_futuro"] * res_adv_copy["pred"]
res_adv_copy["year"] = res_adv_copy.index.year

print(f"\n   {'Año':<8} {'Básicas':>12} {'Avanzadas':>12} {'Ganador':>12}")
print(f"   {'-'*8} {'-'*12} {'-'*12} {'-'*12}")

for year in sorted(set(res_basic_copy["year"].unique()) & set(res_adv_copy["year"].unique())):
    yb = res_basic_copy[res_basic_copy["year"] == year]
    ya = res_adv_copy[res_adv_copy["year"] == year]

    if len(yb) < 5 or len(ya) < 5:
        continue

    r_basic = ((1 + yb["ret"]).cumprod().iloc[-1] - 1) * 100
    r_adv = ((1 + ya["ret"]).cumprod().iloc[-1] - 1) * 100

    ganador = "Avanzadas ✅" if r_adv > r_basic else "Básicas ✅"
    print(f"   {year:<8} {r_basic:>+10.2f}% {r_adv:>+10.2f}%   {ganador}")


# ============================================================
# PARTE 10: CONCLUSIÓN Y DECISIÓN
# ============================================================

print("\n" + "=" * 60)
print("  💡 CONCLUSIÓN")
print("=" * 60)

if m_adv["sharpe"] > m_basic["sharpe"]:
    print(f"""
   Las features avanzadas MEJORARON el Sharpe Ratio
   ({m_basic['sharpe']:.4f} → {m_adv['sharpe']:.4f}).

   El feature engineering profesional funciona.
   Las mejores features nuevas son las de la lista Top 15.
""")
elif m_adv["retorno"] > m_basic["retorno"]:
    print(f"""
   Las features avanzadas MEJORARON el retorno
   ({m_basic['retorno']:+.2f}% → {m_adv['retorno']:+.2f}%).

   Aunque el Sharpe no mejoró, el retorno absoluto sí.
   Hay potencial de mejora con más afinación.
""")
else:
    print(f"""
   Las features avanzadas NO mejoraron claramente el modelo.

   Esto es NORMAL y tiene una lección importante:
   Más features ≠ mejor modelo. A veces, features extra
   añaden ruido en vez de señal. Los quants profesionales
   pasan semanas probando features y descartando las que
   no aportan.

   Lo importante es el PROCESO: crear hipótesis → testear
   → medir → decidir. Eso es exactamente lo que hiciste hoy.
""")

print("=" * 60)
print("  ✅ DÍA 45 COMPLETADO")
print("=" * 60)
