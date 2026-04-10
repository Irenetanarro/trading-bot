"""
DÍA 39: Dashboard y Monitoreo del Trading Bot
==============================================
Bootcamp Quant Trading - Irene Tanarro

Objetivo: Centro de control completo para monitorear
tu bot de trading en Alpaca (paper trading).

Funcionalidades:
1. Estado de cuenta (cash, equity, buying power)
2. Posiciones abiertas con P&L
3. Historial de órdenes
4. Métricas de rendimiento
5. Sistema de alertas
6. Dashboard HTML visual

Requisitos: pip install requests python-dotenv
"""

import requests
import os
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta

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

# Capital inicial (para calcular rendimiento)
CAPITAL_INICIAL = 100000.00

# Umbrales de alertas
ALERTA_PERDIDA_MAXIMA = -5.0      # Alerta si pierdes más del 5%
ALERTA_GANANCIA_OBJETIVO = 10.0   # Alerta si ganas más del 10%
ALERTA_POSICION_GRANDE = 20.0     # Alerta si una posición es >20% del portfolio


# ============================================================
# FUNCIONES DE CONSULTA A ALPACA
# ============================================================

def obtener_cuenta():
    """Obtiene información completa de la cuenta."""
    try:
        response = requests.get(f"{BASE_URL}/v2/account", headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error obteniendo cuenta: {e}")
        return None


def obtener_posiciones():
    """Obtiene todas las posiciones abiertas."""
    try:
        response = requests.get(f"{BASE_URL}/v2/positions", headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error obteniendo posiciones: {e}")
        return []


def obtener_ordenes(limit=50, status="all"):
    """Obtiene historial de órdenes."""
    try:
        params = {
            "limit": limit,
            "status": status,
            "direction": "desc"
        }
        response = requests.get(
            f"{BASE_URL}/v2/orders",
            headers=HEADERS,
            params=params
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error obteniendo órdenes: {e}")
        return []


# ============================================================
# FUNCIONES DE ANÁLISIS Y MÉTRICAS
# ============================================================

def calcular_metricas_cuenta(cuenta):
    """Calcula métricas principales de la cuenta."""
    equity = float(cuenta["equity"])
    cash = float(cuenta["cash"])
    buying_power = float(cuenta["buying_power"])

    # Rendimiento total
    rendimiento_total = ((equity - CAPITAL_INICIAL) / CAPITAL_INICIAL) * 100

    # Porcentaje invertido vs cash
    invertido = equity - cash
    pct_invertido = (invertido / equity) * 100 if equity > 0 else 0
    pct_cash = (cash / equity) * 100 if equity > 0 else 0

    return {
        "equity": equity,
        "cash": cash,
        "buying_power": buying_power,
        "rendimiento_total": rendimiento_total,
        "ganancia_perdida": equity - CAPITAL_INICIAL,
        "pct_invertido": pct_invertido,
        "pct_cash": pct_cash
    }


def analizar_posiciones(posiciones):
    """Analiza posiciones abiertas con P&L detallado."""
    analisis = []

    for pos in posiciones:
        symbol = pos["symbol"]
        qty = float(pos["qty"])
        precio_entrada = float(pos["avg_entry_price"])
        precio_actual = float(pos["current_price"])
        valor_mercado = float(pos["market_value"])
        pl_dolares = float(pos["unrealized_pl"])
        pl_porcentaje = float(pos["unrealized_plpc"]) * 100

        analisis.append({
            "symbol": symbol,
            "qty": qty,
            "precio_entrada": precio_entrada,
            "precio_actual": precio_actual,
            "valor_mercado": valor_mercado,
            "pl_dolares": pl_dolares,
            "pl_porcentaje": pl_porcentaje
        })

    return analisis


def analizar_ordenes(ordenes):
    """Analiza historial de órdenes."""
    resumen = {
        "total": len(ordenes),
        "filled": 0,
        "cancelled": 0,
        "pending": 0,
        "compras": 0,
        "ventas": 0,
        "ordenes_detalle": []
    }

    for orden in ordenes:
        status = orden["status"]
        side = orden["side"]

        if status == "filled":
            resumen["filled"] += 1
        elif status in ["cancelled", "canceled"]:
            resumen["cancelled"] += 1
        elif status in ["new", "accepted", "pending_new", "partially_filled"]:
            resumen["pending"] += 1

        if side == "buy":
            resumen["compras"] += 1
        elif side == "sell":
            resumen["ventas"] += 1

        # Detalle de cada orden
        resumen["ordenes_detalle"].append({
            "symbol": orden["symbol"],
            "side": side,
            "qty": orden.get("filled_qty", orden.get("qty", "?")),
            "type": orden["type"],
            "status": status,
            "created": orden["created_at"][:19].replace("T", " "),
            "filled_price": orden.get("filled_avg_price", "-")
        })

    return resumen


# ============================================================
# SISTEMA DE ALERTAS
# ============================================================

def verificar_alertas(metricas_cuenta, analisis_posiciones, equity):
    """Verifica condiciones de alerta."""
    alertas = []

    # Alerta 1: Pérdida total excesiva
    if metricas_cuenta["rendimiento_total"] < ALERTA_PERDIDA_MAXIMA:
        alertas.append({
            "tipo": "PELIGRO",
            "emoji": "🔴",
            "mensaje": f"Pérdida total del portfolio: {metricas_cuenta['rendimiento_total']:.2f}% (umbral: {ALERTA_PERDIDA_MAXIMA}%)"
        })

    # Alerta 2: Ganancia objetivo alcanzada
    if metricas_cuenta["rendimiento_total"] > ALERTA_GANANCIA_OBJETIVO:
        alertas.append({
            "tipo": "OBJETIVO",
            "emoji": "🟢",
            "mensaje": f"¡Ganancia objetivo alcanzada! {metricas_cuenta['rendimiento_total']:.2f}% (objetivo: {ALERTA_GANANCIA_OBJETIVO}%)"
        })

    # Alerta 3: Posición demasiado grande
    for pos in analisis_posiciones:
        pct_portfolio = (pos["valor_mercado"] / equity) * 100 if equity > 0 else 0
        if pct_portfolio > ALERTA_POSICION_GRANDE:
            alertas.append({
                "tipo": "RIESGO",
                "emoji": "🟡",
                "mensaje": f"{pos['symbol']} es {pct_portfolio:.1f}% del portfolio (máx recomendado: {ALERTA_POSICION_GRANDE}%)"
            })

    # Alerta 4: Posición con pérdida significativa (>10%)
    for pos in analisis_posiciones:
        if pos["pl_porcentaje"] < -10:
            alertas.append({
                "tipo": "STOP LOSS",
                "emoji": "🔴",
                "mensaje": f"{pos['symbol']} perdiendo {pos['pl_porcentaje']:.2f}% - ¡Revisar stop loss!"
            })

    # Alerta 5: Sin alertas = todo bien
    if not alertas:
        alertas.append({
            "tipo": "OK",
            "emoji": "✅",
            "mensaje": "Todo en orden. Sin alertas activas."
        })

    return alertas


# ============================================================
# DASHBOARD EN CONSOLA
# ============================================================

def mostrar_dashboard_consola(metricas, posiciones_analisis, ordenes_resumen, alertas):
    """Muestra dashboard completo en terminal."""

    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("\n" + "=" * 65)
    print("  📊 TRADING BOT DASHBOARD — IRENE TANARRO")
    print(f"  📅 {ahora}")
    print("=" * 65)

    # --- SECCIÓN 1: CUENTA ---
    print("\n💰 ESTADO DE CUENTA")
    print("-" * 45)
    print(f"  Equity (valor total):   ${metricas['equity']:>12,.2f}")
    print(f"  Cash disponible:        ${metricas['cash']:>12,.2f}")
    print(f"  Buying Power:           ${metricas['buying_power']:>12,.2f}")
    print(f"  Capital inicial:        ${CAPITAL_INICIAL:>12,.2f}")
    print("-" * 45)

    # Rendimiento con color
    rend = metricas["rendimiento_total"]
    gp = metricas["ganancia_perdida"]
    emoji_rend = "📈" if gp >= 0 else "📉"
    signo = "+" if gp >= 0 else ""
    print(f"  {emoji_rend} Rendimiento total:    {signo}{rend:.4f}%")
    print(f"  {emoji_rend} Ganancia/Pérdida:     {signo}${gp:,.2f}")
    print(f"  💵 Cash:                {metricas['pct_cash']:.1f}%")
    print(f"  📊 Invertido:           {metricas['pct_invertido']:.1f}%")

    # --- SECCIÓN 2: POSICIONES ---
    print("\n📋 POSICIONES ABIERTAS")
    print("-" * 65)

    if not posiciones_analisis:
        print("  (Sin posiciones abiertas)")
    else:
        print(f"  {'Symbol':<8} {'Qty':>5} {'Entrada':>10} {'Actual':>10} {'P&L $':>10} {'P&L %':>8}")
        print(f"  {'------':<8} {'---':>5} {'-------':>10} {'------':>10} {'-----':>10} {'-----':>8}")

        for pos in posiciones_analisis:
            emoji_pl = "🟢" if pos["pl_dolares"] >= 0 else "🔴"
            signo = "+" if pos["pl_dolares"] >= 0 else ""
            print(f"  {emoji_pl} {pos['symbol']:<6} {pos['qty']:>5.0f} "
                  f"${pos['precio_entrada']:>9.2f} ${pos['precio_actual']:>9.2f} "
                  f"{signo}${pos['pl_dolares']:>8.2f} {signo}{pos['pl_porcentaje']:>6.2f}%")

    # --- SECCIÓN 3: ÓRDENES ---
    print("\n📝 HISTORIAL DE ÓRDENES")
    print("-" * 45)
    print(f"  Total órdenes:     {ordenes_resumen['total']}")
    print(f"  ✅ Ejecutadas:     {ordenes_resumen['filled']}")
    print(f"  ❌ Canceladas:     {ordenes_resumen['cancelled']}")
    print(f"  ⏳ Pendientes:     {ordenes_resumen['pending']}")
    print(f"  🟢 Compras:        {ordenes_resumen['compras']}")
    print(f"  🔴 Ventas:         {ordenes_resumen['ventas']}")

    # Últimas 5 órdenes
    if ordenes_resumen["ordenes_detalle"]:
        print("\n  📜 Últimas órdenes:")
        print(f"  {'Fecha':<20} {'Symbol':<7} {'Lado':<7} {'Qty':>5} {'Precio':>10} {'Estado':<10}")
        print(f"  {'-----':<20} {'------':<7} {'----':<7} {'---':>5} {'------':>10} {'------':<10}")

        for orden in ordenes_resumen["ordenes_detalle"][:5]:
            precio_str = f"${float(orden['filled_price']):>9.2f}" if orden["filled_price"] != "-" else "    -     "
            emoji_lado = "🟢" if orden["side"] == "buy" else "🔴"
            print(f"  {orden['created']:<20} {orden['symbol']:<7} {emoji_lado}{orden['side']:<5} "
                  f"{str(orden['qty']):>5} {precio_str} {orden['status']:<10}")

    # --- SECCIÓN 4: ALERTAS ---
    print("\n🚨 ALERTAS")
    print("-" * 45)
    for alerta in alertas:
        print(f"  {alerta['emoji']} [{alerta['tipo']}] {alerta['mensaje']}")

    print("\n" + "=" * 65)
    print("  💡 Ejecuta este script periódicamente para monitorear tu bot")
    print("=" * 65)


# ============================================================
# DASHBOARD HTML VISUAL
# ============================================================

def generar_dashboard_html(metricas, posiciones_analisis, ordenes_resumen, alertas):
    """Genera un dashboard HTML visual."""

    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rend = metricas["rendimiento_total"]
    gp = metricas["ganancia_perdida"]
    color_rend = "#22c55e" if gp >= 0 else "#ef4444"
    signo = "+" if gp >= 0 else ""

    # Generar filas de posiciones
    filas_posiciones = ""
    if not posiciones_analisis:
        filas_posiciones = '<tr><td colspan="6" style="text-align:center; color:#94a3b8;">Sin posiciones abiertas</td></tr>'
    else:
        for pos in posiciones_analisis:
            color_pl = "#22c55e" if pos["pl_dolares"] >= 0 else "#ef4444"
            s = "+" if pos["pl_dolares"] >= 0 else ""
            filas_posiciones += f"""
            <tr>
                <td><strong>{pos['symbol']}</strong></td>
                <td>{pos['qty']:.0f}</td>
                <td>${pos['precio_entrada']:.2f}</td>
                <td>${pos['precio_actual']:.2f}</td>
                <td style="color:{color_pl}; font-weight:bold;">{s}${pos['pl_dolares']:.2f}</td>
                <td style="color:{color_pl}; font-weight:bold;">{s}{pos['pl_porcentaje']:.2f}%</td>
            </tr>"""

    # Generar filas de órdenes (últimas 10)
    filas_ordenes = ""
    for orden in ordenes_resumen["ordenes_detalle"][:10]:
        color_lado = "#22c55e" if orden["side"] == "buy" else "#ef4444"
        lado_text = "COMPRA" if orden["side"] == "buy" else "VENTA"
        precio_str = f"${float(orden['filled_price']):.2f}" if orden["filled_price"] != "-" else "-"

        # Emoji de estado
        if orden["status"] == "filled":
            estado_html = '<span style="color:#22c55e;">✅ Ejecutada</span>'
        elif orden["status"] in ["cancelled", "canceled"]:
            estado_html = '<span style="color:#ef4444;">❌ Cancelada</span>'
        else:
            estado_html = f'<span style="color:#f59e0b;">⏳ {orden["status"]}</span>'

        filas_ordenes += f"""
        <tr>
            <td>{orden['created']}</td>
            <td><strong>{orden['symbol']}</strong></td>
            <td style="color:{color_lado}; font-weight:bold;">{lado_text}</td>
            <td>{orden['qty']}</td>
            <td>{precio_str}</td>
            <td>{estado_html}</td>
        </tr>"""

    # Generar alertas HTML
    alertas_html = ""
    for alerta in alertas:
        if alerta["tipo"] == "OK":
            bg = "#0f3d24"; border = "#22c55e"
        elif alerta["tipo"] == "PELIGRO" or alerta["tipo"] == "STOP LOSS":
            bg = "#3d1014"; border = "#ef4444"
        elif alerta["tipo"] == "RIESGO":
            bg = "#3d2e07"; border = "#f59e0b"
        else:
            bg = "#0c2d48"; border = "#3b82f6"

        alertas_html += f"""
        <div style="background:{bg}; border-left:4px solid {border};
                    padding:12px 16px; margin-bottom:8px; border-radius:4px;">
            {alerta['emoji']} <strong>[{alerta['tipo']}]</strong> {alerta['mensaje']}
        </div>"""

    # Calcular porcentaje invertido para barra visual
    pct_inv = metricas["pct_invertido"]
    pct_cash = metricas["pct_cash"]

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Bot Dashboard - Irene Tanarro</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #0f172a;
            color: #e2e8f0;
            padding: 20px;
            line-height: 1.6;
        }}

        .dashboard {{
            max-width: 1000px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            padding: 30px 0;
            border-bottom: 2px solid #1e293b;
            margin-bottom: 30px;
        }}

        .header h1 {{
            font-size: 28px;
            color: #f1f5f9;
            margin-bottom: 8px;
        }}

        .header .subtitle {{
            color: #94a3b8;
            font-size: 14px;
        }}

        .cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 30px;
        }}

        .card {{
            background: #1e293b;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }}

        .card .label {{
            font-size: 12px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}

        .card .value {{
            font-size: 24px;
            font-weight: bold;
        }}

        .card .subtext {{
            font-size: 12px;
            color: #64748b;
            margin-top: 4px;
        }}

        .section {{
            background: #1e293b;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
        }}

        .section h2 {{
            font-size: 18px;
            margin-bottom: 16px;
            color: #f1f5f9;
            border-bottom: 1px solid #334155;
            padding-bottom: 8px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th {{
            text-align: left;
            padding: 10px 12px;
            color: #94a3b8;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid #334155;
        }}

        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #1e293b;
            font-size: 14px;
        }}

        tr:hover {{
            background: #263347;
        }}

        .bar-container {{
            display: flex;
            height: 24px;
            border-radius: 12px;
            overflow: hidden;
            margin-top: 12px;
            background: #334155;
        }}

        .bar-invested {{
            background: #3b82f6;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            font-weight: bold;
        }}

        .bar-cash {{
            background: #22c55e;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            font-weight: bold;
        }}

        .footer {{
            text-align: center;
            padding: 20px;
            color: #475569;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="dashboard">

        <!-- HEADER -->
        <div class="header">
            <h1>📊 Trading Bot Dashboard</h1>
            <div class="subtitle">Irene Tanarro — Bootcamp Quant Trading (Día 39/180)</div>
            <div class="subtitle">Última actualización: {ahora}</div>
        </div>

        <!-- TARJETAS PRINCIPALES -->
        <div class="cards">
            <div class="card">
                <div class="label">Equity Total</div>
                <div class="value" style="color:#f1f5f9;">${metricas['equity']:,.2f}</div>
                <div class="subtext">Valor total del portfolio</div>
            </div>
            <div class="card">
                <div class="label">Cash Disponible</div>
                <div class="value" style="color:#22c55e;">${metricas['cash']:,.2f}</div>
                <div class="subtext">{pct_cash:.1f}% del portfolio</div>
            </div>
            <div class="card">
                <div class="label">Rendimiento</div>
                <div class="value" style="color:{color_rend};">{signo}{rend:.4f}%</div>
                <div class="subtext">{signo}${gp:,.2f}</div>
            </div>
            <div class="card">
                <div class="label">Órdenes Ejecutadas</div>
                <div class="value" style="color:#3b82f6;">{ordenes_resumen['filled']}</div>
                <div class="subtext">{ordenes_resumen['compras']} compras / {ordenes_resumen['ventas']} ventas</div>
            </div>
        </div>

        <!-- DISTRIBUCIÓN DEL PORTFOLIO -->
        <div class="section">
            <h2>📊 Distribución del Portfolio</h2>
            <div class="bar-container">
                <div class="bar-invested" style="width:{max(pct_inv, 2):.0f}%;">
                    {pct_inv:.1f}% Invertido
                </div>
                <div class="bar-cash" style="width:{max(pct_cash, 2):.0f}%;">
                    {pct_cash:.1f}% Cash
                </div>
            </div>
        </div>

        <!-- POSICIONES ABIERTAS -->
        <div class="section">
            <h2>📋 Posiciones Abiertas</h2>
            <table>
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Cantidad</th>
                        <th>Precio Entrada</th>
                        <th>Precio Actual</th>
                        <th>P&L ($)</th>
                        <th>P&L (%)</th>
                    </tr>
                </thead>
                <tbody>
                    {filas_posiciones}
                </tbody>
            </table>
        </div>

        <!-- HISTORIAL DE ÓRDENES -->
        <div class="section">
            <h2>📝 Historial de Órdenes (últimas 10)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Fecha</th>
                        <th>Symbol</th>
                        <th>Lado</th>
                        <th>Cantidad</th>
                        <th>Precio</th>
                        <th>Estado</th>
                    </tr>
                </thead>
                <tbody>
                    {filas_ordenes}
                </tbody>
            </table>
        </div>

        <!-- ALERTAS -->
        <div class="section">
            <h2>🚨 Alertas</h2>
            {alertas_html}
        </div>

        <!-- CONFIGURACIÓN DE ALERTAS -->
        <div class="section">
            <h2>⚙️ Configuración</h2>
            <table>
                <tr>
                    <td>Capital Inicial</td>
                    <td><strong>${CAPITAL_INICIAL:,.2f}</strong></td>
                </tr>
                <tr>
                    <td>Alerta Pérdida Máxima</td>
                    <td><strong>{ALERTA_PERDIDA_MAXIMA}%</strong></td>
                </tr>
                <tr>
                    <td>Alerta Ganancia Objetivo</td>
                    <td><strong>{ALERTA_GANANCIA_OBJETIVO}%</strong></td>
                </tr>
                <tr>
                    <td>Alerta Posición Grande</td>
                    <td><strong>{ALERTA_POSICION_GRANDE}%</strong></td>
                </tr>
                <tr>
                    <td>Estrategia Activa</td>
                    <td><strong>Trend Following (MA20/MA50)</strong></td>
                </tr>
                <tr>
                    <td>Risk Management</td>
                    <td><strong>Half Kelly (12.2%) + SL (-10%) + TP (+20%)</strong></td>
                </tr>
            </table>
        </div>

        <!-- FOOTER -->
        <div class="footer">
            <p>Trading Bot Dashboard v1.0 — Bootcamp Quant Trading</p>
            <p>Paper Trading (Alpaca) — No es dinero real</p>
            <p>GitHub: github.com/Irenetanarro/trading-bot</p>
        </div>

    </div>
</body>
</html>"""

    return html


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def main():
    print("\n🔄 Conectando con Alpaca...\n")

    # 1. Obtener datos de Alpaca
    cuenta = obtener_cuenta()
    if not cuenta:
        print("❌ No se pudo conectar con Alpaca. Verifica tus API keys.")
        return

    posiciones = obtener_posiciones()
    ordenes = obtener_ordenes(limit=50, status="all")

    print("✅ Conexión exitosa\n")

    # 2. Calcular métricas
    metricas = calcular_metricas_cuenta(cuenta)
    posiciones_analisis = analizar_posiciones(posiciones)
    ordenes_resumen = analizar_ordenes(ordenes)
    alertas = verificar_alertas(metricas, posiciones_analisis, metricas["equity"])

    # 3. Mostrar dashboard en consola
    mostrar_dashboard_consola(metricas, posiciones_analisis, ordenes_resumen, alertas)

    # 4. Generar dashboard HTML
    html = generar_dashboard_html(metricas, posiciones_analisis, ordenes_resumen, alertas)

    nombre_archivo = "dashboard_trading.html"
    with open(nombre_archivo, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n🌐 Dashboard HTML generado: {nombre_archivo}")
    print("   Ábrelo en tu navegador para ver la versión visual.\n")

    # 5. Resumen rápido
    print("=" * 50)
    print("📊 RESUMEN RÁPIDO")
    print("=" * 50)
    print(f"  Portfolio: ${metricas['equity']:,.2f}")
    signo = "+" if metricas["ganancia_perdida"] >= 0 else ""
    print(f"  P&L: {signo}${metricas['ganancia_perdida']:,.2f} ({signo}{metricas['rendimiento_total']:.4f}%)")
    print(f"  Posiciones abiertas: {len(posiciones_analisis)}")
    print(f"  Órdenes ejecutadas: {ordenes_resumen['filled']}")
    print(f"  Alertas activas: {len([a for a in alertas if a['tipo'] != 'OK'])}")
    print("=" * 50)


if __name__ == "__main__":
    main()