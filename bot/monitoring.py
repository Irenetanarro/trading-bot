"""
DÍA 48: Bot v2 con Logs Profesionales
=======================================
Bootcamp Quant Trading - Irene Tanarro

Añade al bot v2:
1. Log CSV de cada decisión (trading_log.csv)
2. Resumen de sesión guardado
3. Modo "revisar historial" para ver decisiones pasadas

Cada ejecución guarda: fecha, ticker, precio, señales, acción, motivo.
Así puedes revisar si las decisiones fueron buenas o malas.

Requisitos: pip install requests python-dotenv xgboost scikit-learn yfinance pandas numpy
"""

import requests
import os
import csv
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

TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
MAX_POSICIONES = 3
CAPITAL_POR_POSICION = 0.12
STOP_LOSS = -0.10
TAKE_PROFIT = 0.20
CONFIANZA_MINIMA = 0.52

LOG_FILE = "trading_log.csv"
SESSION_LOG = "session_log.txt"

FEATURES = [
    "return_1d", "return_5d", "return_10d", "return_20d",
    "precio_vs_MA5", "precio_vs_MA10", "precio_vs_MA20", "precio_vs_MA50",
    "volatilidad_5d", "volatilidad_10d", "volatilidad_20d",
    "RSI", "MACD", "MACD_signal", "MACD_hist",
    "volumen_vs_media", "rango_diario", "gap_apertura",
    "pos_rango_20d", "dia_semana"
]


# ============================================================
# SISTEMA DE LOGS
# ============================================================

class TradingLogger:
    """Registra cada decisión del bot en CSV y texto."""

    def __init__(self, log_file=LOG_FILE):
        self.log_file = log_file
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_logs = []

        # Crear CSV si no existe
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "session_id", "timestamp", "ticker", "precio",
                    "ma20", "ma50", "rsi", "prob_sube",
                    "senal_tf", "senal_ml", "senal_final",
                    "accion_ejecutada", "qty", "motivo",
                    "equity", "cash"
                ])

    def registrar_analisis(self, datos, equity=0, cash=0):
        """Registra el análisis de un ticker."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        fila = [
            self.session_id,
            timestamp,
            datos.get("ticker", ""),
            f"{datos.get('precio', 0):.2f}",
            f"{datos.get('ma20', 0):.2f}",
            f"{datos.get('ma50', 0):.2f}",
            f"{datos.get('rsi', 0):.1f}",
            f"{datos.get('prob_sube', 0):.4f}",
            datos.get("senal_tf", ""),
            datos.get("senal_ml", ""),
            datos.get("senal_final", ""),
            datos.get("accion", "NINGUNA"),
            datos.get("qty", 0),
            datos.get("motivo", ""),
            f"{equity:.2f}",
            f"{cash:.2f}"
        ]

        # Escribir en CSV
        with open(self.log_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(fila)

        # Guardar en memoria para resumen
        self.session_logs.append(datos)

    def guardar_resumen_sesion(self, resumen_texto):
        """Guarda resumen de la sesión en archivo de texto."""
        with open(SESSION_LOG, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"SESIÓN: {self.session_id}\n")
            f.write(f"{'='*60}\n")
            f.write(resumen_texto)
            f.write(f"\n")


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
        return None


def analizar_ticker(ticker, df):
    df_train = df.dropna(subset=FEATURES + ["target"]).iloc[:-1]
    if len(df_train) < 200:
        return None

    modelo = XGBClassifier(
        n_estimators=100, max_depth=2, learning_rate=0.05,
        subsample=0.7, colsample_bytree=0.7, reg_alpha=1.0,
        reg_lambda=2.0, min_child_weight=10, gamma=0.1,
        random_state=42, eval_metric="logloss", verbosity=0
    )
    modelo.fit(df_train[FEATURES], df_train["target"])

    ultimo = df.dropna(subset=FEATURES).iloc[-1]
    X_pred = df.dropna(subset=FEATURES)[FEATURES].iloc[-1:]
    pred = modelo.predict(X_pred)[0]
    prob = modelo.predict_proba(X_pred)[0]

    ma20 = ultimo["MA20"]
    ma50 = ultimo["MA50"]
    senal_tf = "COMPRAR" if ma20 > ma50 else "VENDER"
    senal_ml = "COMPRAR" if pred == 1 and prob[1] >= CONFIANZA_MINIMA else "NO COMPRAR"

    if senal_tf == "COMPRAR" and senal_ml == "COMPRAR":
        senal_final = "COMPRAR"
    elif senal_tf == "VENDER":
        senal_final = "VENDER"
    else:
        senal_final = "ESPERAR"

    return {
        "ticker": ticker,
        "precio": ultimo["Close"],
        "ma20": ma20,
        "ma50": ma50,
        "rsi": ultimo["RSI"],
        "prob_sube": prob[1],
        "senal_tf": senal_tf,
        "senal_ml": senal_ml,
        "senal_final": senal_final
    }


# ============================================================
# REVISAR HISTORIAL
# ============================================================

def revisar_historial():
    """Muestra el historial de decisiones del bot."""

    print("\n" + "=" * 65)
    print("  📜 HISTORIAL DE DECISIONES DEL BOT")
    print("=" * 65)

    if not os.path.exists(LOG_FILE):
        print("\n   (Sin historial. Ejecuta el bot primero.)")
        return

    df = pd.read_csv(LOG_FILE)

    if len(df) == 0:
        print("\n   (Sin registros aún.)")
        return

    # Resumen general
    total_sesiones = df["session_id"].nunique()
    total_registros = len(df)
    primera = df["timestamp"].iloc[0]
    ultima = df["timestamp"].iloc[-1]

    print(f"\n   📊 Resumen General:")
    print(f"      Total sesiones:  {total_sesiones}")
    print(f"      Total registros: {total_registros}")
    print(f"      Primera sesión:  {primera}")
    print(f"      Última sesión:   {ultima}")

    # Acciones por tipo
    acciones = df["accion_ejecutada"].value_counts()
    print(f"\n   ⚡ Acciones ejecutadas:")
    for accion, count in acciones.items():
        print(f"      {accion}: {count}")

    # Señales por ticker
    print(f"\n   📡 Señales finales por ticker:")
    for ticker in df["ticker"].unique():
        ticker_data = df[df["ticker"] == ticker]
        compras = (ticker_data["senal_final"] == "COMPRAR").sum()
        ventas = (ticker_data["senal_final"] == "VENDER").sum()
        esperas = (ticker_data["senal_final"] == "ESPERAR").sum()
        print(f"      {ticker}: {compras} compras, {ventas} ventas, {esperas} esperas")

    # Últimas 10 decisiones
    print(f"\n   📋 Últimas 10 decisiones:")
    print(f"   {'Fecha':<20} {'Ticker':<7} {'Precio':>8} {'TF':<8} {'ML':<12} {'Final':<10} {'Acción':<10}")
    print(f"   {'-'*20} {'-'*7} {'-'*8} {'-'*8} {'-'*12} {'-'*10} {'-'*10}")

    for _, row in df.tail(10).iterrows():
        print(f"   {str(row['timestamp']):<20} {row['ticker']:<7} ${float(row['precio']):>7.2f} "
              f"{row['senal_tf']:<8} {row['senal_ml']:<12} {row['senal_final']:<10} {row['accion_ejecutada']:<10}")

    # Veces que ML cambió la decisión
    ml_cambio = ((df["senal_tf"] == "COMPRAR") & (df["senal_final"] == "ESPERAR")).sum()
    ml_confirmo = ((df["senal_tf"] == "COMPRAR") & (df["senal_final"] == "COMPRAR")).sum()
    print(f"\n   🧠 Impacto del ML:")
    print(f"      ML bloqueó compra de TF: {ml_cambio} veces")
    print(f"      ML confirmó compra de TF: {ml_confirmo} veces")


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def ejecutar_bot():
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger = TradingLogger()

    print("\n" + "=" * 65)
    print("  🤖 BOT v2 CON LOGS PROFESIONALES")
    print(f"  📅 {ahora}")
    print(f"  📋 Session ID: {logger.session_id}")
    print("=" * 65)

    # 1. Conectar
    print("\n🔌 Conectando con Alpaca...")
    cuenta = obtener_cuenta()
    if not cuenta:
        print("   ❌ No se pudo conectar.")
        return

    equity = float(cuenta["equity"])
    cash = float(cuenta["cash"])
    print(f"   ✅ Conectado | Equity: ${equity:,.2f} | Cash: ${cash:,.2f}")

    # 2. Posiciones
    print("\n📋 POSICIONES ACTUALES:")
    posiciones = obtener_posiciones()
    posiciones_dict = {}

    if not posiciones:
        print("   (Sin posiciones abiertas)")
    else:
        for pos in posiciones:
            sym = pos["symbol"]
            pl = float(pos["unrealized_pl"])
            pl_pct = float(pos["unrealized_plpc"]) * 100
            signo = "+" if pl >= 0 else ""
            emoji = "🟢" if pl >= 0 else "🔴"
            posiciones_dict[sym] = pos
            print(f"   {emoji} {sym}: {float(pos['qty']):.0f} acc | {signo}${pl:.2f} ({signo}{pl_pct:.2f}%)")

    # 3. Protecciones
    ventas_proteccion = []
    for sym, pos in posiciones_dict.items():
        pl_pct = float(pos["unrealized_plpc"])
        if pl_pct <= STOP_LOSS:
            print(f"   🔴 STOP LOSS: {sym} → VENDER")
            ventas_proteccion.append(sym)
        elif pl_pct >= TAKE_PROFIT:
            print(f"   🟢 TAKE PROFIT: {sym} → VENDER")
            ventas_proteccion.append(sym)

    for sym in ventas_proteccion:
        qty = int(float(posiciones_dict[sym]["qty"]))
        orden = enviar_orden(sym, qty, "sell")
        if orden:
            logger.registrar_analisis({
                "ticker": sym, "precio": float(posiciones_dict[sym]["current_price"]),
                "ma20": 0, "ma50": 0, "rsi": 0, "prob_sube": 0,
                "senal_tf": "-", "senal_ml": "-", "senal_final": "PROTECCION",
                "accion": "VENTA_PROTECCION", "qty": qty,
                "motivo": f"SL/TP activado ({float(posiciones_dict[sym]['unrealized_plpc'])*100:.1f}%)"
            }, equity, cash)
            del posiciones_dict[sym]

    # 4. Analizar tickers
    print("\n" + "=" * 65)
    print("  📡 ANÁLISIS DE SEÑALES")
    print("=" * 65)

    senales_compra = []
    senales_venta = []
    resumen_texto = f"Fecha: {ahora}\nEquity: ${equity:,.2f} | Cash: ${cash:,.2f}\n\n"

    for ticker in TICKERS:
        print(f"\n   ⏳ {ticker}...", end="")
        df = preparar_datos(ticker)
        if df is None:
            print(f" ❌ Sin datos")
            continue

        resultado = analizar_ticker(ticker, df)
        if resultado is None:
            print(f" ❌ Datos insuficientes")
            continue

        emoji_final = {"COMPRAR": "✅", "VENDER": "🔴", "ESPERAR": "⏸️"}
        print(f"\r   {ticker:<7} ${resultado['precio']:>8.2f} | "
              f"TF: {resultado['senal_tf']:<8} | ML: {resultado['senal_ml']:<12} "
              f"({resultado['prob_sube']*100:.1f}%) | "
              f"RSI: {resultado['rsi']:.0f} | "
              f"{emoji_final.get(resultado['senal_final'], '?')} {resultado['senal_final']}")

        resumen_texto += (f"{ticker}: ${resultado['precio']:.2f} | "
                         f"TF={resultado['senal_tf']} ML={resultado['senal_ml']} "
                         f"→ {resultado['senal_final']}\n")

        if resultado["senal_final"] == "COMPRAR":
            senales_compra.append(resultado)
        elif resultado["senal_final"] == "VENDER":
            senales_venta.append(resultado)

        # Registrar en log (sin acción aún)
        log_data = {
            "ticker": ticker,
            "precio": resultado["precio"],
            "ma20": resultado["ma20"],
            "ma50": resultado["ma50"],
            "rsi": resultado["rsi"],
            "prob_sube": resultado["prob_sube"],
            "senal_tf": resultado["senal_tf"],
            "senal_ml": resultado["senal_ml"],
            "senal_final": resultado["senal_final"],
            "accion": "NINGUNA",
            "qty": 0,
            "motivo": ""
        }

        # Determinar acción
        if resultado["senal_final"] == "VENDER" and ticker in posiciones_dict:
            log_data["accion"] = "PENDIENTE_VENTA"
            log_data["motivo"] = "Death Cross"
        elif resultado["senal_final"] == "COMPRAR" and ticker not in posiciones_dict:
            log_data["accion"] = "PENDIENTE_COMPRA"
            log_data["motivo"] = "Golden Cross + ML confirma"

        logger.registrar_analisis(log_data, equity, cash)

    # 5. Ejecutar ventas
    print(f"\n" + "=" * 65)
    print(f"  ⚡ EJECUTANDO DECISIONES")
    print("=" * 65)

    ventas_ok = 0
    for senal in senales_venta:
        sym = senal["ticker"]
        if sym in posiciones_dict:
            qty = int(float(posiciones_dict[sym]["qty"]))
            print(f"\n   🔴 Vendiendo {qty} {sym}")
            orden = enviar_orden(sym, qty, "sell")
            if orden:
                print(f"   ✅ Venta ejecutada")
                ventas_ok += 1
                resumen_texto += f"  → VENDIDO {qty} {sym}\n"

    # 6. Ejecutar compras
    posiciones_actuales = len(posiciones_dict) - ventas_ok
    slots = MAX_POSICIONES - max(posiciones_actuales, 0)
    compras_ok = 0

    if slots > 0 and senales_compra:
        senales_compra.sort(key=lambda x: x["prob_sube"], reverse=True)
        capital_por_pos = cash * CAPITAL_POR_POSICION

        for senal in senales_compra[:slots]:
            sym = senal["ticker"]
            if sym in posiciones_dict:
                continue

            qty = int(capital_por_pos / senal["precio"])
            if qty > 0:
                print(f"\n   🟢 Comprando {qty} {sym} a ~${senal['precio']:.2f} (ML: {senal['prob_sube']*100:.1f}%)")
                orden = enviar_orden(sym, qty, "buy")
                if orden:
                    print(f"   ✅ Compra ejecutada")
                    compras_ok += 1
                    resumen_texto += f"  → COMPRADO {qty} {sym}\n"
    elif not senales_compra:
        print(f"\n   ⏸️ Sin señales de compra hoy")

    # 7. Resumen
    resumen_texto += f"\nCompras: {compras_ok} | Ventas: {ventas_ok + len(ventas_proteccion)}\n"
    logger.guardar_resumen_sesion(resumen_texto)

    print(f"\n" + "=" * 65)
    print(f"  📊 RESUMEN DE SESIÓN")
    print("=" * 65)
    print(f"\n   Session ID:         {logger.session_id}")
    print(f"   Acciones analizadas: {len(TICKERS)}")
    print(f"   Señales compra:     {len(senales_compra)}")
    print(f"   Señales venta:      {len(senales_venta)}")
    print(f"   Compras ejecutadas: {compras_ok}")
    print(f"   Ventas ejecutadas:  {ventas_ok + len(ventas_proteccion)}")
    print(f"\n   📁 Log guardado en: {LOG_FILE}")
    print(f"   📁 Resumen en:      {SESSION_LOG}")

    # 8. Mostrar historial
    print()
    revisar_historial()

    print(f"\n" + "=" * 65)
    print(f"  ✅ DÍA 48 COMPLETADO")
    print("=" * 65)


# ============================================================
# EJECUTAR
# ============================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "historial":
        revisar_historial()
    else:
        ejecutar_bot()
