import requests
import os
import pandas as pd
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = "https://paper-api.alpaca.markets"
HEADERS = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY,
    "Content-Type": "application/json"
}

CAPITAL_INICIAL = 100000.00


# --- 1. Cuenta actual ---
r = requests.get(f"{BASE_URL}/v2/account", headers=HEADERS)
cuenta = r.json()
equity_actual = float(cuenta["equity"])

# --- 2. Historial de órdenes ejecutadas ---
r = requests.get(f"{BASE_URL}/v2/orders", headers=HEADERS,
                 params={"status": "filled", "limit": 100, "direction": "asc"})
ordenes = r.json()

print("=" * 55)
print("  📊 ANÁLISIS DE MÉTRICAS — TU BOT v2")
print("=" * 55)

if len(ordenes) == 0:
    print("\n⚠️ No tienes órdenes ejecutadas todavía.")
    exit()

# --- 3. Construir historial de trades (pares compra-venta) ---
trades = []
posiciones_abiertas = {}  # symbol → lista de compras

for o in ordenes:
    symbol = o["symbol"]
    qty = float(o["filled_qty"])
    precio = float(o["filled_avg_price"])
    fecha = o["filled_at"][:10]
    
    if o["side"] == "buy":
        if symbol not in posiciones_abiertas:
            posiciones_abiertas[symbol] = []
        posiciones_abiertas[symbol].append({"qty": qty, "precio": precio, "fecha": fecha})
    
    else:  # sell
        if symbol in posiciones_abiertas and posiciones_abiertas[symbol]:
            compra = posiciones_abiertas[symbol].pop(0)
            pl = (precio - compra["precio"]) * qty
            pl_pct = (precio - compra["precio"]) / compra["precio"] * 100
            trades.append({
                "symbol": symbol,
                "compra": compra["precio"],
                "venta": precio,
                "qty": qty,
                "pl": pl,
                "pl_pct": pl_pct,
                "fecha_compra": compra["fecha"],
                "fecha_venta": fecha
            })

# --- 4. Calcular métricas ---
print(f"\n💰 RETORNO TOTAL")
print(f"   Equity actual:    ${equity_actual:,.2f}")
print(f"   Capital inicial:  ${CAPITAL_INICIAL:,.2f}")
pl_total = equity_actual - CAPITAL_INICIAL
retorno_total = (pl_total / CAPITAL_INICIAL) * 100
signo = "+" if pl_total >= 0 else ""
print(f"   P&L:              {signo}${pl_total:,.2f}")
print(f"   Retorno:          {signo}{retorno_total:.4f}%")

if len(trades) == 0:
    print("\n⚠️ No hay trades completos (compra+venta) todavía.")
    print("   Necesitas al menos 1 venta para calcular el resto.")
    exit()

print(f"\n📋 TRADES COMPLETOS: {len(trades)}")
print(f"   {'Ticker':<7} {'Compra':>10} {'Venta':>10} {'P&L':>10} {'P&L %':>8}")
print(f"   {'-'*7} {'-'*10} {'-'*10} {'-'*10} {'-'*8}")
for t in trades:
    s = "+" if t["pl"] >= 0 else ""
    emoji = "🟢" if t["pl"] >= 0 else "🔴"
    print(f"   {emoji}{t['symbol']:<5} ${t['compra']:>9.2f} ${t['venta']:>9.2f} {s}${t['pl']:>8.2f} {s}{t['pl_pct']:>6.2f}%")

# --- Win Rate ---
trades_ganadores = sum(1 for t in trades if t["pl"] > 0)
win_rate = (trades_ganadores / len(trades)) * 100
print(f"\n🎯 WIN RATE")
print(f"   Trades ganadores: {trades_ganadores}/{len(trades)}")
print(f"   Win Rate:         {win_rate:.2f}%")

# --- Sharpe Ratio (necesita retornos) ---
retornos = [t["pl_pct"] / 100 for t in trades]
if len(retornos) >= 2:
    retornos_arr = np.array(retornos)
    if retornos_arr.std() > 0:
        sharpe = (retornos_arr.mean() / retornos_arr.std()) * np.sqrt(252)
        print(f"\n📐 SHARPE RATIO")
        print(f"   Sharpe: {sharpe:.4f}")
        if sharpe > 2:
            print(f"   → Excelente")
        elif sharpe > 1:
            print(f"   → Bueno")
        elif sharpe > 0:
            print(f"   → Mediocre (pero positivo)")
        else:
            print(f"   → Negativo (el bot pierde)")
    else:
        print(f"\n📐 SHARPE RATIO: no calculable (std=0, muy pocos trades)")
else:
    print(f"\n📐 SHARPE RATIO: necesitas ≥2 trades para calcularlo")

# --- Max Drawdown ---
# Simulamos el equity a lo largo del tiempo
equity_history = [CAPITAL_INICIAL]
capital = CAPITAL_INICIAL
for t in trades:
    capital += t["pl"]
    equity_history.append(capital)

equity_arr = np.array(equity_history)
peaks = np.maximum.accumulate(equity_arr)
drawdowns = (equity_arr - peaks) / peaks * 100
max_dd = drawdowns.min()

print(f"\n📉 MAX DRAWDOWN")
print(f"   Max Drawdown: {max_dd:.2f}%")
if max_dd > -10:
    print(f"   → Excelente (< -10%)")
elif max_dd > -20:
    print(f"   → Bueno (< -20%)")
else:
    print(f"   → Elevado (> -20%)")

# --- Resumen final ---
print(f"\n" + "=" * 55)
print(f"  📊 RESUMEN EJECUTIVO")
print(f"=" * 55)
print(f"   Retorno Total:    {signo}{retorno_total:.4f}%")
print(f"   Win Rate:         {win_rate:.2f}%")
if len(retornos) >= 2 and retornos_arr.std() > 0:
    print(f"   Sharpe Ratio:     {sharpe:.4f}")
print(f"   Max Drawdown:     {max_dd:.2f}%")
print(f"   Trades completos: {len(trades)}")
print(f"=" * 55)