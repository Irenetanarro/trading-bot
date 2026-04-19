"""
DÍA 47: Bot v2 Multi-Acción
============================
Bootcamp Quant Trading - Irene Tanarro

Bot v2 expandido: analiza 5 acciones, entrena XGBoost para cada una,
genera señales TF + ML, y reparte capital entre las que dan señal de compra.

Acciones: AAPL, MSFT, GOOGL, AMZN, TSLA
Capital: Se reparte equitativamente entre señales activas

Requisitos: pip install requests python-dotenv xgboost scikit-learn yfinance pandas numpy
"""

import requests
import os
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

# Acciones a analizar
TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

# Parámetros
MAX_POSICIONES = 3           # Máximo 3 acciones a la vez (no meter todo)
CAPITAL_POR_POSICION = 0.12  # 12% del capital por acción (Half Kelly)
STOP_LOSS = -0.10
TAKE_PROFIT = 0.20
CONFIANZA_MINIMA = 0.52

FEATURES = [
    "return_1d", "return_5d", "return_10d", "return_20d",
    "precio_vs_MA5", "precio_vs_MA10", "precio_vs_MA20", "precio_vs_MA50",
    "volatilidad_5d", "volatilidad_10d", "volatilidad_20d",
    "RSI", "MACD", "MACD_signal", "MACD_hist",
    "volumen_vs_media", "rango_diario", "gap_apertura",
    "pos_rango_20d", "dia_semana"
]


# ============================================================
# FUNCIONES DE ALPACA
# ============================================================

def obtener_cuenta():
    try:
        r = requests.get(f"{BASE_URL}/v2/account", headers=HEADERS)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"   ❌ Error cuenta: {e}")
        return None


def obtener_posiciones():
    try:
        r = requests.get(f"{BASE_URL}/v2/positions", headers=HEADERS)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"   ❌ Error posiciones: {e}")
        return []


def enviar_orden(symbol, qty, side):
    try:
        orden = {
            "symbol": symbol,
            "qty": str(qty),
            "side": side,
            "type": "market",
            "time_in_force": "day"
        }
        r = requests.post(f"{BASE_URL}/v2/orders", headers=HEADERS, json=orden)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"   ❌ Error orden {symbol}: {e}")
        return None


# ============================================================
# FUNCIONES DE DATOS Y ML
# ============================================================

def preparar_datos(ticker):
    """Descarga datos y crea features para un ticker."""
    try:
        data = yf.download(ticker, start="2020-01-01", progress=False)

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        if len(data) < 100:
            return None

        df = data.copy()

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

        df["target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)

        return df

    except Exception as e:
        print(f"   ❌ Error descargando {ticker}: {e}")
        return None


def analizar_ticker(ticker, df):
    """Entrena modelo y genera señales para un ticker."""

    df_train = df.dropna(subset=FEATURES + ["target"]).iloc[:-1]

    if len(df_train) < 200:
        return None

    # Entrenar XGBoost
    X = df_train[FEATURES]
    y = df_train["target"]

    modelo = XGBClassifier(
        n_estimators=100, max_depth=2, learning_rate=0.05,
        subsample=0.7, colsample_bytree=0.7, reg_alpha=1.0,
        reg_lambda=2.0, min_child_weight=10, gamma=0.1,
        random_state=42, eval_metric="logloss", verbosity=0
    )
    modelo.fit(X, y)

    # Datos del último día
    ultimo = df.dropna(subset=FEATURES).iloc[-1]

    # Señal Trend Following
    ma20 = ultimo["MA20"]
    ma50 = ultimo["MA50"]
    señal_tf = "COMPRAR" if ma20 > ma50 else "VENDER"

    # Señal XGBoost
    X_pred = df.dropna(subset=FEATURES)[FEATURES].iloc[-1:]
    pred = modelo.predict(X_pred)[0]
    prob = modelo.predict_proba(X_pred)[0]
    prob_sube = prob[1]

    señal_ml = "COMPRAR" if pred == 1 and prob_sube >= CONFIANZA_MINIMA else "NO COMPRAR"

    # Señal combinada
    if señal_tf == "COMPRAR" and señal_ml == "COMPRAR":
        señal_final = "COMPRAR"
    elif señal_tf == "VENDER":
        señal_final = "VENDER"
    else:
        señal_final = "ESPERAR"

    return {
        "ticker": ticker,
        "precio": ultimo["Close"],
        "ma20": ma20,
        "ma50": ma50,
        "rsi": ultimo["RSI"],
        "señal_tf": señal_tf,
        "señal_ml": señal_ml,
        "prob_sube": prob_sube,
        "señal_final": señal_final
    }


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def ejecutar_bot():
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("\n" + "=" * 65)
    print("  🤖 BOT v2 MULTI-ACCIÓN: TF + XGBOOST")
    print(f"  📅 {ahora}")
    print(f"  📊 Analizando: {', '.join(TICKERS)}")
    print("=" * 65)

    # 1. Conectar con Alpaca
    print("\n🔌 Conectando con Alpaca...")
    cuenta = obtener_cuenta()
    if not cuenta:
        print("   ❌ No se pudo conectar.")
        return

    equity = float(cuenta["equity"])
    cash = float(cuenta["cash"])
    print(f"   ✅ Conectado | Equity: ${equity:,.2f} | Cash: ${cash:,.2f}")

    # 2. Posiciones actuales
    print("\n📋 POSICIONES ACTUALES:")
    posiciones = obtener_posiciones()
    posiciones_dict = {}

    if not posiciones:
        print("   (Sin posiciones abiertas)")
    else:
        print(f"\n   {'Ticker':<8} {'Qty':>5} {'Entrada':>10} {'Actual':>10} {'P&L':>12} {'P&L %':>8}")
        print(f"   {'------':<8} {'---':>5} {'-------':>10} {'------':>10} {'---':>12} {'-----':>8}")

        for pos in posiciones:
            sym = pos["symbol"]
            qty = float(pos["qty"])
            entrada = float(pos["avg_entry_price"])
            actual = float(pos["current_price"])
            pl = float(pos["unrealized_pl"])
            pl_pct = float(pos["unrealized_plpc"]) * 100
            signo = "+" if pl >= 0 else ""
            emoji = "🟢" if pl >= 0 else "🔴"

            posiciones_dict[sym] = pos
            print(f"   {emoji} {sym:<6} {qty:>5.0f} ${entrada:>9.2f} ${actual:>9.2f} {signo}${pl:>10.2f} {signo}{pl_pct:>6.2f}%")

    # 3. Verificar stop loss / take profit en posiciones existentes
    print("\n🛡️ VERIFICANDO PROTECCIONES:")
    ventas_proteccion = []

    for sym, pos in posiciones_dict.items():
        pl_pct = float(pos["unrealized_plpc"])

        if pl_pct <= STOP_LOSS:
            print(f"   🔴 STOP LOSS: {sym} perdiendo {pl_pct*100:.2f}% → VENDER")
            ventas_proteccion.append(sym)
        elif pl_pct >= TAKE_PROFIT:
            print(f"   🟢 TAKE PROFIT: {sym} ganando {pl_pct*100:.2f}% → VENDER")
            ventas_proteccion.append(sym)

    if not ventas_proteccion:
        print("   ✅ Sin alertas de protección")

    # Ejecutar ventas de protección
    for sym in ventas_proteccion:
        qty = int(float(posiciones_dict[sym]["qty"]))
        orden = enviar_orden(sym, qty, "sell")
        if orden:
            print(f"   ✅ Vendido {qty} {sym} (protección)")
            del posiciones_dict[sym]

    # 4. Analizar cada ticker
    print("\n" + "=" * 65)
    print("  📡 ANÁLISIS DE SEÑALES")
    print("=" * 65)

    señales_compra = []
    señales_venta = []

    print(f"\n   {'Ticker':<8} {'Precio':>10} {'MA20':>10} {'MA50':>10} {'RSI':>6} {'TF':>10} {'ML':>12} {'Prob':>7} {'FINAL':>10}")
    print(f"   {'------':<8} {'------':>10} {'----':>10} {'----':>10} {'---':>6} {'--':>10} {'--':>12} {'----':>7} {'-----':>10}")

    for ticker in TICKERS:
        print(f"\n   ⏳ Analizando {ticker}...", end="")
        df = preparar_datos(ticker)

        if df is None:
            print(f" ❌ Sin datos")
            continue

        resultado = analizar_ticker(ticker, df)

        if resultado is None:
            print(f" ❌ Datos insuficientes")
            continue

        # Emojis
        emoji_tf = "🟢" if resultado["señal_tf"] == "COMPRAR" else "🔴"
        emoji_ml = "🟢" if resultado["señal_ml"] == "COMPRAR" else "🔴"

        if resultado["señal_final"] == "COMPRAR":
            emoji_final = "✅ COMPRAR"
        elif resultado["señal_final"] == "VENDER":
            emoji_final = "🔴 VENDER"
        else:
            emoji_final = "⏸️ ESPERAR"

        print(f"\r   {ticker:<8} ${resultado['precio']:>9.2f} ${resultado['ma20']:>9.2f} ${resultado['ma50']:>9.2f} "
              f"{resultado['rsi']:>5.1f} {emoji_tf} {resultado['señal_tf']:<7} "
              f"{emoji_ml} {resultado['señal_ml']:<9} {resultado['prob_sube']*100:>5.1f}% "
              f"{emoji_final}")

        if resultado["señal_final"] == "COMPRAR":
            señales_compra.append(resultado)
        elif resultado["señal_final"] == "VENDER":
            señales_venta.append(resultado)

    # 5. Ejecutar ventas (señal de vender posiciones que tenemos)
    print(f"\n" + "=" * 65)
    print(f"  ⚡ EJECUTANDO DECISIONES")
    print("=" * 65)

    ventas_ejecutadas = 0
    for señal in señales_venta:
        sym = señal["ticker"]
        if sym in posiciones_dict:
            qty = int(float(posiciones_dict[sym]["qty"]))
            print(f"\n   🔴 VENDER {qty} {sym} (Death Cross)")
            orden = enviar_orden(sym, qty, "sell")
            if orden:
                print(f"   ✅ Venta ejecutada")
                ventas_ejecutadas += 1
                del posiciones_dict[sym]

    # 6. Ejecutar compras (máximo MAX_POSICIONES)
    posiciones_actuales = len(posiciones_dict)
    slots_disponibles = MAX_POSICIONES - posiciones_actuales

    compras_ejecutadas = 0

    if slots_disponibles > 0 and señales_compra:
        # Ordenar por probabilidad de subida (la más confiada primero)
        señales_compra.sort(key=lambda x: x["prob_sube"], reverse=True)

        # Solo comprar las mejores hasta llenar slots
        compras_a_hacer = señales_compra[:slots_disponibles]

        # Capital por posición
        capital_por_pos = cash * CAPITAL_POR_POSICION

        for señal in compras_a_hacer:
            sym = señal["ticker"]
            precio = señal["precio"]

            # No comprar si ya tenemos posición
            if sym in posiciones_dict:
                print(f"\n   ⏸️ {sym}: ya tienes posición, manteniendo")
                continue

            qty = int(capital_por_pos / precio)

            if qty > 0:
                costo = qty * precio
                print(f"\n   🟢 COMPRAR {qty} {sym} a ~${precio:.2f}")
                print(f"      Capital: ${costo:,.2f} | ML confianza: {señal['prob_sube']*100:.1f}%")

                orden = enviar_orden(sym, qty, "buy")
                if orden:
                    print(f"      ✅ Compra ejecutada")
                    compras_ejecutadas += 1
                    posiciones_dict[sym] = True  # Marcar como comprado
            else:
                print(f"\n   ⚠️ {sym}: capital insuficiente para 1 acción (${precio:.2f})")

    elif slots_disponibles <= 0 and señales_compra:
        print(f"\n   ⚠️ Ya tienes {posiciones_actuales} posiciones (máx: {MAX_POSICIONES})")
        print(f"      Señales de compra ignoradas: {', '.join(s['ticker'] for s in señales_compra)}")

    elif not señales_compra:
        print(f"\n   ⏸️ Sin señales de compra hoy")

    # 7. Resumen final
    print(f"\n" + "=" * 65)
    print(f"  📊 RESUMEN DE SESIÓN")
    print("=" * 65)

    print(f"\n   Acciones analizadas: {len(TICKERS)}")
    print(f"   Señales de compra:  {len(señales_compra)} ({', '.join(s['ticker'] for s in señales_compra) if señales_compra else 'ninguna'})")
    print(f"   Señales de venta:   {len(señales_venta)} ({', '.join(s['ticker'] for s in señales_venta) if señales_venta else 'ninguna'})")
    print(f"   Compras ejecutadas: {compras_ejecutadas}")
    print(f"   Ventas ejecutadas:  {ventas_ejecutadas + len(ventas_proteccion)}")

    n_pos_final = len([p for p in posiciones_dict.values() if p is not True])
    print(f"\n   Configuración:")
    print(f"   · Máx posiciones:    {MAX_POSICIONES}")
    print(f"   · Capital/posición:  {CAPITAL_POR_POSICION*100}% (Half Kelly)")
    print(f"   · Stop Loss:         {STOP_LOSS*100}%")
    print(f"   · Take Profit:       {TAKE_PROFIT*100}%")
    print(f"   · Confianza mínima:  {CONFIANZA_MINIMA*100}%")

    print(f"\n" + "=" * 65)
    print(f"  ✅ DÍA 47 COMPLETADO")
    print("=" * 65)


# ============================================================
# EJECUTAR
# ============================================================

if __name__ == "__main__":
    ejecutar_bot()
