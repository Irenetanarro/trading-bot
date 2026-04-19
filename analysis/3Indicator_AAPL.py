import yfinance as yf
import pandas as pd

# Descargar datos
data = yf.download("AAPL", period="6mo", progress=False)
if data.columns.nlevels > 1:
    data.columns = data.columns.get_level_values(0)

# --- RSI ---
delta = data["Close"].diff()
ganancia = delta.where(delta > 0, 0).rolling(14).mean()
perdida = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = ganancia / perdida
data["RSI"] = 100 - (100 / (1 + rs))

# --- MACD ---
ema12 = data["Close"].ewm(span=12).mean()
ema26 = data["Close"].ewm(span=26).mean()
data["MACD"] = ema12 - ema26
data["MACD_signal"] = data["MACD"].ewm(span=9).mean()
data["MACD_hist"] = data["MACD"] - data["MACD_signal"]

# --- Volatilidad (20 días) ---
data["retorno_diario"] = data["Close"].pct_change()
data["volatilidad_20d"] = data["retorno_diario"].rolling(20).std() * 100  # en %

# Mostrar valores actuales
rsi = float(data["RSI"].iloc[-1])
macd = float(data["MACD"].iloc[-1])
macd_signal = float(data["MACD_signal"].iloc[-1])
vol = float(data["volatilidad_20d"].iloc[-1])

print(f"📊 AAPL — Indicadores actuales:")
print(f"")
print(f"RSI: {rsi:.1f}", end="")
if rsi > 70:
    print(" → 🔴 SOBRECOMPRADA")
elif rsi < 30:
    print(" → 🟢 SOBREVENDIDA")
else:
    print(" → ⚪ Neutral")

print(f"")
print(f"MACD: {macd:.2f}")
print(f"Signal: {macd_signal:.2f}")
if macd > macd_signal:
    print(" → 🟢 Momentum alcista")
else:
    print(" → 🔴 Momentum bajista")

print(f"")
print(f"Volatilidad 20 días: {vol:.2f}%")
if vol > 3:
    print(" → ⚠️ Alta volatilidad")
elif vol < 1:
    print(" → ✅ Baja volatilidad")
else:
    print(" → 📊 Volatilidad normal")