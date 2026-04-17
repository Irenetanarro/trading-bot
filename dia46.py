"""
DÍA 46: Bot v2 — Trend Following + XGBoost
============================================
Bootcamp Quant Trading - Irene Tanarro

Bot v1 (Día 37-38): Solo Trend Following MA20/MA50
Bot v2 (Hoy): Trend Following + XGBoost como filtro de confirmación

Lógica:
- TF dice COMPRAR + XGBoost dice SUBE → COMPRAR
- TF dice COMPRAR + XGBoost dice BAJA → NO COMPRAR (ML filtra)
- TF dice VENDER → VENDER (no necesita confirmación ML)

Requisitos: pip install requests python-dotenv xgboost scikit-learn yfinance pandas numpy
"""

import requests
import os
import json
import yfinance as yf
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from dotenv import load_dotenv
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")


# ============================================================
# CONFIGURACIÓN
# ============================================================

load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = "https://paper-api.alpaca.markets"

HEADERS = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY,
    "Content-Type": "application/json"
}

# Parámetros del bot
TICKER = "AAPL"
CAPITAL_INICIAL = 100000.00
HALF_KELLY = 0.122          # 12.2% del capital por operación
STOP_LOSS = -0.10           # Vender si pierde 10%
TAKE_PROFIT = 0.20          # Vender si gana 20%
CONFIANZA_MINIMA = 0.52     # XGBoost debe tener al menos 52% de confianza


# ============================================================
# PARTE 1: FUNCIONES DE ALPACA
# ============================================================

def obtener_cuenta():
    """Obtiene estado de la cuenta."""
    try:
        r = requests.get(f"{BASE_URL}/v2/account", headers=HEADERS)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"   ❌ Error cuenta: {e}")
        return None


def obtener_posiciones():
    """Obtiene posiciones abiertas."""
    try:
        r = requests.get(f"{BASE_URL}/v2/positions", headers=HEADERS)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"   ❌ Error posiciones: {e}")
        return []


def obtener_posicion(symbol):
    """Obtiene posición de un símbolo específico."""
    try:
        r = requests.get(f"{BASE_URL}/v2/positions/{symbol}", headers=HEADERS)
        if r.status_code == 404:
            return None  # No hay posición
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return None


def enviar_orden(symbol, qty, side, order_type="market"):
    """Envía una orden a Alpaca."""
    try:
        orden = {
            "symbol": symbol,
            "qty": str(qty),
            "side": side,
            "type": order_type,
            "time_in_force": "day"
        }
        r = requests.post(f"{BASE_URL}/v2/orders", headers=HEADERS, json=orden)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"   ❌ Error orden: {e}")
        return None


# ============================================================
# PARTE 2: DESCARGAR DATOS Y CREAR FEATURES
# ============================================================

def descargar_y_preparar_datos(ticker):
    """Descarga datos y crea todas las features para ML."""

    data = yf.download(ticker, start="2020-01-01", progress=False)

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

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

    # Target (para entrenar)
    df["target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)

    return df


# ============================================================
# PARTE 3: ENTRENAR MODELO XGBOOST
# ============================================================

def entrenar_modelo(df, features):
    """Entrena XGBoost con todos los datos disponibles (menos el último día)."""

    df_train = df.dropna(subset=features + ["target"]).iloc[:-1]  # Excluir último día

    X = df_train[features]
    y = df_train["target"]

    modelo = XGBClassifier(
        n_estimators=100, max_depth=2, learning_rate=0.05,
        subsample=0.7, colsample_bytree=0.7, reg_alpha=1.0,
        reg_lambda=2.0, min_child_weight=10, gamma=0.1,
        random_state=42, eval_metric="logloss", verbosity=0
    )

    modelo.fit(X, y)
    return modelo


# ============================================================
# PARTE 4: GENERAR SEÑALES
# ============================================================

def generar_señales(df, modelo, features):
    """Genera señales combinando Trend Following + XGBoost."""

    ultimo = df.dropna(subset=features).iloc[-1]

    # --- Señal Trend Following ---
    ma20 = ultimo["MA20"]
    ma50 = ultimo["MA50"]

    if ma20 > ma50:
        señal_tf = "COMPRAR"
        tf_detalle = f"MA20 ({ma20:.2f}) > MA50 ({ma50:.2f}) → Golden Cross"
    else:
        señal_tf = "VENDER"
        tf_detalle = f"MA20 ({ma20:.2f}) <= MA50 ({ma50:.2f}) → Death Cross"

    # --- Señal XGBoost ---
    X_pred = df.dropna(subset=features)[features].iloc[-1:]
    prediccion = modelo.predict(X_pred)[0]
    probabilidad = modelo.predict_proba(X_pred)[0]
    prob_sube = probabilidad[1]
    prob_baja = probabilidad[0]

    if prediccion == 1 and prob_sube >= CONFIANZA_MINIMA:
        señal_ml = "COMPRAR"
        ml_detalle = f"XGBoost predice SUBE ({prob_sube*100:.1f}% confianza)"
    else:
        señal_ml = "NO COMPRAR"
        ml_detalle = f"XGBoost predice BAJA ({prob_baja*100:.1f}%) o confianza insuficiente"

    # --- Señal combinada ---
    if señal_tf == "COMPRAR" and señal_ml == "COMPRAR":
        señal_final = "COMPRAR"
        motivo = "TF + ML coinciden → señal fuerte de compra"
    elif señal_tf == "VENDER":
        señal_final = "VENDER"
        motivo = "TF dice vender → salir de posición"
    else:
        señal_final = "ESPERAR"
        motivo = "TF dice comprar pero ML no confirma → esperar"

    return {
        "señal_tf": señal_tf,
        "tf_detalle": tf_detalle,
        "señal_ml": señal_ml,
        "ml_detalle": ml_detalle,
        "señal_final": señal_final,
        "motivo": motivo,
        "prob_sube": prob_sube,
        "prob_baja": prob_baja,
        "precio_actual": ultimo["Close"],
        "rsi": ultimo["RSI"],
        "ma20": ma20,
        "ma50": ma50
    }


# ============================================================
# PARTE 5: VERIFICAR STOP LOSS / TAKE PROFIT
# ============================================================

def verificar_protecciones(posicion):
    """Verifica si hay que vender por stop loss o take profit."""

    if posicion is None:
        return None

    precio_entrada = float(posicion["avg_entry_price"])
    precio_actual = float(posicion["current_price"])
    pl_pct = float(posicion["unrealized_plpc"])

    if pl_pct <= STOP_LOSS:
        return {
            "accion": "STOP_LOSS",
            "motivo": f"Pérdida de {pl_pct*100:.2f}% (límite: {STOP_LOSS*100}%)",
            "precio_entrada": precio_entrada,
            "precio_actual": precio_actual
        }
    elif pl_pct >= TAKE_PROFIT:
        return {
            "accion": "TAKE_PROFIT",
            "motivo": f"Ganancia de {pl_pct*100:.2f}% (objetivo: {TAKE_PROFIT*100}%)",
            "precio_entrada": precio_entrada,
            "precio_actual": precio_actual
        }

    return None


# ============================================================
# PARTE 6: CALCULAR TAMAÑO DE POSICIÓN (HALF KELLY)
# ============================================================

def calcular_qty(cash, precio_actual):
    """Calcula cuántas acciones comprar con Half Kelly."""
    capital_asignar = cash * HALF_KELLY
    qty = int(capital_asignar / precio_actual)
    return max(qty, 0)


# ============================================================
# PARTE 7: EJECUTAR BOT
# ============================================================

def ejecutar_bot():
    """Función principal del bot v2."""

    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("\n" + "=" * 60)
    print("  🤖 BOT v2: TREND FOLLOWING + XGBOOST")
    print(f"  📅 {ahora}")
    print("=" * 60)

    # 1. Conectar con Alpaca
    print("\n🔌 Conectando con Alpaca...")
    cuenta = obtener_cuenta()
    if not cuenta:
        print("   ❌ No se pudo conectar. Verifica API keys.")
        return

    equity = float(cuenta["equity"])
    cash = float(cuenta["cash"])
    print(f"   ✅ Conectado")
    print(f"   💰 Equity: ${equity:,.2f}")
    print(f"   💵 Cash:   ${cash:,.2f}")

    # 2. Verificar posición actual
    print(f"\n📋 Verificando posición de {TICKER}...")
    posicion = obtener_posicion(TICKER)

    if posicion:
        qty_actual = float(posicion["qty"])
        precio_entrada = float(posicion["avg_entry_price"])
        precio_actual = float(posicion["current_price"])
        pl = float(posicion["unrealized_pl"])
        pl_pct = float(posicion["unrealized_plpc"]) * 100
        signo = "+" if pl >= 0 else ""
        print(f"   📊 Posición abierta: {qty_actual:.0f} {TICKER}")
        print(f"   📊 Entrada: ${precio_entrada:.2f} | Actual: ${precio_actual:.2f}")
        print(f"   📊 P&L: {signo}${pl:.2f} ({signo}{pl_pct:.2f}%)")
    else:
        print(f"   📊 Sin posición abierta en {TICKER}")

    # 3. Verificar stop loss / take profit
    if posicion:
        print(f"\n🛡️ Verificando protecciones...")
        proteccion = verificar_protecciones(posicion)
        if proteccion:
            print(f"   🚨 {proteccion['accion']}: {proteccion['motivo']}")
            print(f"   📊 Vendiendo toda la posición...")

            qty_vender = int(float(posicion["qty"]))
            orden = enviar_orden(TICKER, qty_vender, "sell")
            if orden:
                print(f"   ✅ Orden de venta enviada: {qty_vender} {TICKER}")
                print(f"   📋 Orden ID: {orden['id']}")
            else:
                print(f"   ❌ Error enviando orden de venta")
            return
        else:
            print(f"   ✅ Sin alertas de protección")

    # 4. Descargar datos y entrenar modelo
    print(f"\n📥 Descargando datos de {TICKER}...")
    df = descargar_y_preparar_datos(TICKER)
    print(f"   ✅ {len(df)} días de datos")

    features = [
        "return_1d", "return_5d", "return_10d", "return_20d",
        "precio_vs_MA5", "precio_vs_MA10", "precio_vs_MA20", "precio_vs_MA50",
        "volatilidad_5d", "volatilidad_10d", "volatilidad_20d",
        "RSI", "MACD", "MACD_signal", "MACD_hist",
        "volumen_vs_media", "rango_diario", "gap_apertura",
        "pos_rango_20d", "dia_semana"
    ]

    print(f"\n🧠 Entrenando XGBoost...")
    modelo = entrenar_modelo(df, features)
    print(f"   ✅ Modelo entrenado con {len(df)-51} muestras")

    # 5. Generar señales
    print(f"\n📡 Generando señales...")
    señales = generar_señales(df, modelo, features)

    print(f"\n   🔀 SEÑALES:")
    print(f"   ┌─────────────────────────────────────────────")
    print(f"   │ Trend Following: {señales['señal_tf']}")
    print(f"   │   {señales['tf_detalle']}")
    print(f"   │")
    print(f"   │ XGBoost ML:      {señales['señal_ml']}")
    print(f"   │   {señales['ml_detalle']}")
    print(f"   │")
    print(f"   │ 📊 Datos actuales:")
    print(f"   │   Precio: ${señales['precio_actual']:.2f}")
    print(f"   │   RSI:    {señales['rsi']:.1f}")
    print(f"   │   MA20:   ${señales['ma20']:.2f}")
    print(f"   │   MA50:   ${señales['ma50']:.2f}")
    print(f"   │")
    print(f"   │ ═══════════════════════════════════════")
    print(f"   │ SEÑAL FINAL: {señales['señal_final']}")
    print(f"   │ {señales['motivo']}")
    print(f"   └─────────────────────────────────────────────")

    # 6. Ejecutar acción
    print(f"\n⚡ EJECUTANDO DECISIÓN...")

    if señales["señal_final"] == "COMPRAR" and posicion is None:
        # Calcular cantidad
        qty = calcular_qty(cash, señales["precio_actual"])

        if qty > 0:
            print(f"   🟢 Comprando {qty} {TICKER} a ~${señales['precio_actual']:.2f}")
            print(f"   💰 Capital asignado: ${qty * señales['precio_actual']:,.2f} ({HALF_KELLY*100}% Half Kelly)")

            orden = enviar_orden(TICKER, qty, "buy")
            if orden:
                print(f"   ✅ Orden de compra enviada")
                print(f"   📋 Orden ID: {orden['id']}")
            else:
                print(f"   ❌ Error enviando orden")
        else:
            print(f"   ⚠️ Capital insuficiente para comprar")

    elif señales["señal_final"] == "VENDER" and posicion is not None:
        qty_vender = int(float(posicion["qty"]))
        print(f"   🔴 Vendiendo {qty_vender} {TICKER}")

        orden = enviar_orden(TICKER, qty_vender, "sell")
        if orden:
            print(f"   ✅ Orden de venta enviada")
            print(f"   📋 Orden ID: {orden['id']}")
        else:
            print(f"   ❌ Error enviando orden")

    elif señales["señal_final"] == "COMPRAR" and posicion is not None:
        print(f"   ⏸️ Señal de compra pero ya tienes posición. Manteniendo.")

    elif señales["señal_final"] == "ESPERAR":
        if posicion:
            print(f"   ⏸️ ML no confirma compra. Manteniendo posición actual.")
        else:
            print(f"   ⏸️ ML no confirma compra. Sin acción.")

    elif señales["señal_final"] == "VENDER" and posicion is None:
        print(f"   ⏸️ Señal de venta pero no tienes posición. Sin acción.")

    # 7. Resumen final
    print(f"\n" + "=" * 60)
    print(f"  📊 RESUMEN BOT v2")
    print(f"=" * 60)
    print(f"   Ticker:         {TICKER}")
    print(f"   Señal TF:       {señales['señal_tf']}")
    print(f"   Señal ML:       {señales['señal_ml']} ({señales['prob_sube']*100:.1f}% sube)")
    print(f"   Señal Final:    {señales['señal_final']}")
    print(f"   Protecciones:   SL {STOP_LOSS*100}% | TP {TAKE_PROFIT*100}%")
    print(f"   Position Size:  Half Kelly {HALF_KELLY*100}%")

    # Comparar con bot v1
    print(f"\n   🔄 BOT v1 vs v2:")
    print(f"      v1: Solo Trend Following → {señales['señal_tf']}")
    print(f"      v2: TF + XGBoost filtro  → {señales['señal_final']}")
    if señales["señal_tf"] != señales["señal_final"]:
        print(f"      ⚡ ML CAMBIÓ la decisión del bot")
    else:
        print(f"      ✅ ML confirmó la decisión de TF")

    print(f"\n" + "=" * 60)
    print(f"  ✅ DÍA 46 COMPLETADO")
    print(f"=" * 60)


# ============================================================
# EJECUTAR
# ============================================================

if __name__ == "__main__":
    ejecutar_bot()
