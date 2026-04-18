"""
DÍA 49: Reporte Completo del Bot v2
=====================================
Bootcamp Quant Trading - Irene Tanarro

Genera un reporte profesional con:
1. Estado de cuenta actual
2. Historial completo de órdenes en Alpaca
3. Análisis de rendimiento
4. Estado de señales actuales de las 5 acciones
5. Reporte HTML visual

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

TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
CAPITAL_INICIAL = 100000.00

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
    except:
        return None


def obtener_posiciones():
    try:
        r = requests.get(f"{BASE_URL}/v2/positions", headers=HEADERS)
        r.raise_for_status()
        return r.json()
    except:
        return []


def obtener_ordenes(limit=100):
    try:
        r = requests.get(f"{BASE_URL}/v2/orders", headers=HEADERS,
                        params={"limit": limit, "status": "all", "direction": "desc"})
        r.raise_for_status()
        return r.json()
    except:
        return []


# ============================================================
# FUNCIONES DE ML
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
    except:
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
    senal_ml = "COMPRAR" if pred == 1 and prob[1] >= 0.52 else "NO COMPRAR"

    if senal_tf == "COMPRAR" and senal_ml == "COMPRAR":
        senal_final = "COMPRAR"
    elif senal_tf == "VENDER":
        senal_final = "VENDER"
    else:
        senal_final = "ESPERAR"

    return {
        "ticker": ticker,
        "precio": float(ultimo["Close"]),
        "ma20": float(ma20),
        "ma50": float(ma50),
        "rsi": float(ultimo["RSI"]),
        "prob_sube": float(prob[1]),
        "senal_tf": senal_tf,
        "senal_ml": senal_ml,
        "senal_final": senal_final
    }


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def main():
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("=" * 65)
    print("  📊 DÍA 49: REPORTE COMPLETO DEL BOT v2")
    print(f"  📅 {ahora}")
    print("=" * 65)

    # ---- 1. CUENTA ----
    print("\n🔌 Conectando con Alpaca...")
    cuenta = obtener_cuenta()
    if not cuenta:
        print("   ❌ No se pudo conectar.")
        return

    equity = float(cuenta["equity"])
    cash = float(cuenta["cash"])
    buying_power = float(cuenta["buying_power"])
    rendimiento = ((equity - CAPITAL_INICIAL) / CAPITAL_INICIAL) * 100
    ganancia = equity - CAPITAL_INICIAL

    print(f"\n💰 ESTADO DE CUENTA")
    print(f"   Equity:       ${equity:,.2f}")
    print(f"   Cash:         ${cash:,.2f}")
    print(f"   Buying Power: ${buying_power:,.2f}")
    print(f"   Rendimiento:  {'+' if ganancia >= 0 else ''}{rendimiento:.4f}%")
    print(f"   P&L:          {'+' if ganancia >= 0 else ''}${ganancia:,.2f}")

    # ---- 2. POSICIONES ----
    print(f"\n📋 POSICIONES ABIERTAS")
    posiciones = obtener_posiciones()

    if not posiciones:
        print("   (Sin posiciones abiertas — 100% cash)")
    else:
        for pos in posiciones:
            pl = float(pos["unrealized_pl"])
            pl_pct = float(pos["unrealized_plpc"]) * 100
            signo = "+" if pl >= 0 else ""
            print(f"   {pos['symbol']}: {float(pos['qty']):.0f} acc | "
                  f"Entrada ${float(pos['avg_entry_price']):.2f} | "
                  f"Actual ${float(pos['current_price']):.2f} | "
                  f"P&L {signo}${pl:.2f} ({signo}{pl_pct:.2f}%)")

    # ---- 3. HISTORIAL DE ÓRDENES ----
    print(f"\n📝 HISTORIAL DE ÓRDENES")
    ordenes = obtener_ordenes(limit=50)

    filled = [o for o in ordenes if o["status"] == "filled"]
    cancelled = [o for o in ordenes if o["status"] in ["cancelled", "canceled"]]

    print(f"   Total órdenes:   {len(ordenes)}")
    print(f"   Ejecutadas:      {len(filled)}")
    print(f"   Canceladas:      {len(cancelled)}")

    compras = [o for o in filled if o["side"] == "buy"]
    ventas = [o for o in filled if o["side"] == "sell"]
    print(f"   Compras:         {len(compras)}")
    print(f"   Ventas:          {len(ventas)}")

    if filled:
        print(f"\n   📋 Detalle de órdenes ejecutadas:")
        print(f"   {'Fecha':<20} {'Ticker':<7} {'Lado':<7} {'Qty':>5} {'Precio':>10}")
        print(f"   {'-'*20} {'-'*7} {'-'*7} {'-'*5} {'-'*10}")

        for o in filled[:20]:
            fecha = o["filled_at"][:19].replace("T", " ") if o.get("filled_at") else o["created_at"][:19].replace("T", " ")
            precio = f"${float(o['filled_avg_price']):.2f}" if o.get("filled_avg_price") else "-"
            emoji = "🟢" if o["side"] == "buy" else "🔴"
            print(f"   {fecha:<20} {o['symbol']:<7} {emoji}{o['side']:<5} "
                  f"{o.get('filled_qty', o.get('qty', '?')):>5} {precio:>10}")

    # ---- 4. SEÑALES ACTUALES ----
    print(f"\n" + "=" * 65)
    print(f"  📡 SEÑALES ACTUALES — 5 ACCIONES")
    print("=" * 65)

    senales = []
    for ticker in TICKERS:
        print(f"   ⏳ Analizando {ticker}...", end="")
        df = preparar_datos(ticker)
        if df is None:
            print(f" ❌")
            continue

        resultado = analizar_ticker(ticker, df)
        if resultado is None:
            print(f" ❌")
            continue

        senales.append(resultado)
        emoji = {"COMPRAR": "✅", "VENDER": "🔴", "ESPERAR": "⏸️"}
        print(f"\r   {ticker:<7} ${resultado['precio']:>8.2f} | RSI {resultado['rsi']:>5.1f} | "
              f"TF: {resultado['senal_tf']:<8} ML: {resultado['senal_ml']:<12} "
              f"→ {emoji.get(resultado['senal_final'], '?')} {resultado['senal_final']}")

    # Resumen de señales
    n_compra = sum(1 for s in senales if s["senal_final"] == "COMPRAR")
    n_venta = sum(1 for s in senales if s["senal_final"] == "VENDER")
    n_espera = sum(1 for s in senales if s["senal_final"] == "ESPERAR")

    print(f"\n   📊 Resumen: {n_compra} comprar, {n_venta} vender, {n_espera} esperar")

    # ---- 5. GENERAR HTML ----
    print(f"\n🌐 Generando reporte HTML...")

    # Filas de posiciones
    filas_pos = ""
    if not posiciones:
        filas_pos = '<tr><td colspan="6" style="text-align:center;color:#64748b;">100% en cash — sin posiciones abiertas</td></tr>'
    else:
        for pos in posiciones:
            pl = float(pos["unrealized_pl"])
            pl_pct = float(pos["unrealized_plpc"]) * 100
            color = "#22c55e" if pl >= 0 else "#ef4444"
            signo = "+" if pl >= 0 else ""
            filas_pos += f"""<tr>
                <td><strong>{pos['symbol']}</strong></td>
                <td>{float(pos['qty']):.0f}</td>
                <td>${float(pos['avg_entry_price']):.2f}</td>
                <td>${float(pos['current_price']):.2f}</td>
                <td style="color:{color};font-weight:bold">{signo}${pl:.2f}</td>
                <td style="color:{color};font-weight:bold">{signo}{pl_pct:.2f}%</td></tr>"""

    # Filas de órdenes
    filas_ord = ""
    for o in filled[:15]:
        fecha = o.get("filled_at", o["created_at"])[:10]
        precio = f"${float(o['filled_avg_price']):.2f}" if o.get("filled_avg_price") else "-"
        color_lado = "#22c55e" if o["side"] == "buy" else "#ef4444"
        lado = "COMPRA" if o["side"] == "buy" else "VENTA"
        filas_ord += f"""<tr>
            <td>{fecha}</td>
            <td><strong>{o['symbol']}</strong></td>
            <td style="color:{color_lado};font-weight:bold">{lado}</td>
            <td>{o.get('filled_qty', o.get('qty', '?'))}</td>
            <td>{precio}</td></tr>"""

    # Filas de señales
    filas_sen = ""
    for s in senales:
        color_tf = "#22c55e" if s["senal_tf"] == "COMPRAR" else "#ef4444"
        color_ml = "#22c55e" if s["senal_ml"] == "COMPRAR" else "#ef4444"
        if s["senal_final"] == "COMPRAR":
            color_final = "#22c55e"
        elif s["senal_final"] == "VENDER":
            color_final = "#ef4444"
        else:
            color_final = "#f59e0b"

        filas_sen += f"""<tr>
            <td><strong>{s['ticker']}</strong></td>
            <td>${s['precio']:.2f}</td>
            <td>{s['rsi']:.0f}</td>
            <td style="color:{color_tf}">{s['senal_tf']}</td>
            <td style="color:{color_ml}">{s['senal_ml']}</td>
            <td>{s['prob_sube']*100:.1f}%</td>
            <td style="color:{color_final};font-weight:bold">{s['senal_final']}</td></tr>"""

    color_rend = "#22c55e" if ganancia >= 0 else "#ef4444"
    signo_r = "+" if ganancia >= 0 else ""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bot v2 Reporte - Irene Tanarro</title>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:'Segoe UI',sans-serif; background:#0f172a; color:#e2e8f0; padding:20px; }}
        .container {{ max-width:950px; margin:0 auto; }}
        .header {{ text-align:center; padding:30px 0; border-bottom:2px solid #1e293b; margin-bottom:24px; }}
        .header h1 {{ font-size:26px; color:#f1f5f9; margin-bottom:6px; }}
        .header .sub {{ color:#94a3b8; font-size:13px; }}
        .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px; margin-bottom:24px; }}
        .card {{ background:#1e293b; border-radius:12px; padding:18px; text-align:center; }}
        .card .val {{ font-size:22px; font-weight:bold; margin-bottom:4px; }}
        .card .lbl {{ font-size:11px; color:#94a3b8; text-transform:uppercase; letter-spacing:0.5px; }}
        .section {{ background:#1e293b; border-radius:12px; padding:24px; margin-bottom:16px; }}
        .section h2 {{ font-size:16px; margin-bottom:14px; border-bottom:1px solid #334155; padding-bottom:8px; }}
        table {{ width:100%; border-collapse:collapse; }}
        th {{ text-align:left; padding:8px 10px; color:#94a3b8; font-size:11px; text-transform:uppercase;
              letter-spacing:0.5px; border-bottom:1px solid #334155; }}
        td {{ padding:8px 10px; border-bottom:1px solid #1e293b; font-size:13px; }}
        tr:hover {{ background:#263347; }}
        .badge {{ display:inline-block; font-size:10px; padding:3px 8px; border-radius:3px;
                  font-weight:bold; letter-spacing:0.5px; }}
        .badge-buy {{ background:rgba(34,197,94,0.15); color:#22c55e; }}
        .badge-sell {{ background:rgba(239,68,68,0.15); color:#ef4444; }}
        .badge-wait {{ background:rgba(245,158,11,0.15); color:#f59e0b; }}
        .tech {{ font-size:11px; color:#64748b; margin-top:16px; }}
        .footer {{ text-align:center; padding:20px; color:#475569; font-size:11px; }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🤖 Bot v2 — Reporte de Trading</h1>
        <div class="sub">Irene Tanarro | Bootcamp Quant Trading | Día 49/180</div>
        <div class="sub">Generado: {ahora}</div>
    </div>

    <div class="cards">
        <div class="card">
            <div class="val" style="color:#f1f5f9">${equity:,.2f}</div>
            <div class="lbl">Equity</div>
        </div>
        <div class="card">
            <div class="val" style="color:#22c55e">${cash:,.2f}</div>
            <div class="lbl">Cash Disponible</div>
        </div>
        <div class="card">
            <div class="val" style="color:{color_rend}">{signo_r}{rendimiento:.4f}%</div>
            <div class="lbl">Rendimiento</div>
        </div>
        <div class="card">
            <div class="val" style="color:#3b82f6">{len(filled)}</div>
            <div class="lbl">Órdenes Ejecutadas</div>
        </div>
        <div class="card">
            <div class="val" style="color:#a78bfa">{len(posiciones)}</div>
            <div class="lbl">Posiciones Abiertas</div>
        </div>
    </div>

    <div class="section">
        <h2>📋 Posiciones Abiertas</h2>
        <table>
            <thead><tr><th>Ticker</th><th>Qty</th><th>Entrada</th><th>Actual</th><th>P&L $</th><th>P&L %</th></tr></thead>
            <tbody>{filas_pos}</tbody>
        </table>
    </div>

    <div class="section">
        <h2>📡 Señales Actuales — {ahora[:10]}</h2>
        <table>
            <thead><tr><th>Ticker</th><th>Precio</th><th>RSI</th><th>Trend Follow</th><th>XGBoost ML</th><th>Prob. Sube</th><th>Señal Final</th></tr></thead>
            <tbody>{filas_sen}</tbody>
        </table>
        <div class="tech" style="margin-top:12px;">
            Señales: <span class="badge badge-buy">COMPRAR</span> = TF + ML coinciden &nbsp;
            <span class="badge badge-sell">VENDER</span> = Death Cross &nbsp;
            <span class="badge badge-wait">ESPERAR</span> = ML no confirma
        </div>
    </div>

    <div class="section">
        <h2>📝 Historial de Órdenes</h2>
        <table>
            <thead><tr><th>Fecha</th><th>Ticker</th><th>Lado</th><th>Qty</th><th>Precio</th></tr></thead>
            <tbody>{filas_ord if filas_ord else '<tr><td colspan="5" style="text-align:center;color:#64748b;">Sin órdenes ejecutadas aún</td></tr>'}</tbody>
        </table>
    </div>

    <div class="section">
        <h2>⚙️ Configuración del Bot v2</h2>
        <table>
            <tr><td>Estrategia</td><td><strong>Trend Following (MA20/MA50) + XGBoost ML</strong></td></tr>
            <tr><td>Acciones</td><td><strong>{', '.join(TICKERS)}</strong></td></tr>
            <tr><td>Máx. posiciones simultáneas</td><td><strong>3</strong></td></tr>
            <tr><td>Position sizing</td><td><strong>Half Kelly (12.2%)</strong></td></tr>
            <tr><td>Stop Loss</td><td><strong>-10%</strong></td></tr>
            <tr><td>Take Profit</td><td><strong>+20%</strong></td></tr>
            <tr><td>Confianza mínima ML</td><td><strong>52%</strong></td></tr>
            <tr><td>Modelo ML</td><td><strong>XGBoost (100 árboles, max_depth=2)</strong></td></tr>
            <tr><td>Features</td><td><strong>20 (retornos, MAs, RSI, MACD, volumen, volatilidad)</strong></td></tr>
        </table>
    </div>

    <div class="section">
        <h2>📚 Stack Tecnológico</h2>
        <table>
            <tr><td>Lenguaje</td><td><strong>Python 3.14</strong></td></tr>
            <tr><td>Broker</td><td><strong>Alpaca (Paper Trading)</strong></td></tr>
            <tr><td>Datos</td><td><strong>yfinance</strong></td></tr>
            <tr><td>ML</td><td><strong>XGBoost + scikit-learn</strong></td></tr>
            <tr><td>Deep Learning</td><td><strong>PyTorch (LSTM testeado)</strong></td></tr>
            <tr><td>Repositorio</td><td><strong>github.com/Irenetanarro/tradingbot</strong></td></tr>
        </table>
    </div>

    <div class="footer">
        <p>Bot v2 Reporte — Bootcamp Quant Trading — Irene Tanarro 2026</p>
        <p>Paper Trading · No es dinero real · Día 49 de 180</p>
    </div>
</div>
</body>
</html>"""

    nombre_html = "reporte_bot_v2.html"
    with open(nombre_html, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"   ✅ Reporte generado: {nombre_html}")

    # ---- RESUMEN CONSOLA ----
    print(f"\n" + "=" * 65)
    print(f"  📊 RESUMEN EJECUTIVO")
    print("=" * 65)
    print(f"""
   Portfolio:          ${equity:,.2f}
   Rendimiento:        {signo_r}{rendimiento:.4f}% ({signo_r}${ganancia:,.2f})
   Posiciones:         {len(posiciones)} abiertas
   Órdenes ejecutadas: {len(filled)} ({len(compras)} compras, {len(ventas)} ventas)

   Señales hoy:        {n_compra} comprar, {n_venta} vender, {n_espera} esperar
   Estado del mercado:  {'Mayoría alcista ✅' if n_compra > n_venta else 'Mayoría bajista 🔴' if n_venta > n_compra else 'Mixto ⏸️'}

   Bot v2 activo con:
   · Trend Following MA20/MA50 + XGBoost ML
   · 5 acciones monitoreadas
   · Half Kelly + Stop Loss + Take Profit
   · Logs profesionales
""")

    print("=" * 65)
    print("  ✅ DÍA 49 COMPLETADO")
    print("=" * 65)


if __name__ == "__main__":
    main()
