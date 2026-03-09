import yfinance as yf
import numpy as np

ticker = "AAPL"
data = yf.download(ticker, start="2020-01-01")

# Calcular retornos diarios
data['Retorno'] = data['Close'].pct_change()

print("\n" + "="*70)
print("SHARPE RATIO - APPLE (2020-2026)")
print("="*70)

# BUY AND HOLD
print("\n[1] BUY AND HOLD")
print("-" * 70)

# Calcular métricas
retornos = data['Retorno'].dropna()

retorno_promedio_diario = retornos.mean()
retorno_anual = retorno_promedio_diario * 252  # 252 días de trading al año

volatilidad_diaria = retornos.std()
volatilidad_anual = volatilidad_diaria * np.sqrt(252)

tasa_libre_riesgo = 0.04  # 4% anual (bonos del gobierno)

sharpe_ratio = (retorno_anual - tasa_libre_riesgo) / volatilidad_anual

print("Retorno anualizado:", round(retorno_anual * 100, 2), "%")
print("Volatilidad anualizada:", round(volatilidad_anual * 100, 2), "%")
print("Sharpe Ratio:", round(sharpe_ratio, 3))

if sharpe_ratio < 0:
    calificacion = "MALO - Perdiste dinero"
elif sharpe_ratio < 1:
    calificacion = "MEDIOCRE - Mucho riesgo para poco retorno"
elif sharpe_ratio < 2:
    calificacion = "BUENO - Estrategia solida"
elif sharpe_ratio < 3:
    calificacion = "EXCELENTE - Nivel hedge fund"
else:
    calificacion = "EXTRAORDINARIO - Posible overfitting"

print("Calificacion:", calificacion)

# Ahora calculemos para las estrategias del día 12
print("\n" + "="*70)
print("COMPARACION DE SHARPE RATIOS")
print("="*70)

# Para esto necesitamos simular los retornos de cada estrategia
# Vamos a hacerlo simple: calculamos los retornos cuando estamos invertidos

# ESTRATEGIA MEDIAS MOVILES
data['MA20'] = data['Close'].rolling(window=20).mean()
data['MA50'] = data['Close'].rolling(window=50).mean()
data['Signal_MA'] = 0
data.loc[data['MA20'] > data['MA50'], 'Signal_MA'] = 1

# Retornos solo cuando estamos invertidos (Signal = 1)
data['Retorno_MA'] = data['Retorno'] * data['Signal_MA']

retornos_ma = data['Retorno_MA'].dropna()
retorno_anual_ma = retornos_ma.mean() * 252
volatilidad_anual_ma = retornos_ma.std() * np.sqrt(252)
sharpe_ma = (retorno_anual_ma - tasa_libre_riesgo) / volatilidad_anual_ma

print("\n[2] MEDIAS MOVILES")
print("-" * 70)
print("Retorno anualizado:", round(retorno_anual_ma * 100, 2), "%")
print("Volatilidad anualizada:", round(volatilidad_anual_ma * 100, 2), "%")
print("Sharpe Ratio:", round(sharpe_ma, 3))

# ESTRATEGIA RSI
def calcular_rsi(data, periodo=14):
    delta = data['Close'].diff()
    ganancias = delta.where(delta > 0, 0)
    perdidas = -delta.where(delta < 0, 0)
    avg_ganancias = ganancias.rolling(window=periodo).mean()
    avg_perdidas = perdidas.rolling(window=periodo).mean()
    rs = avg_ganancias / avg_perdidas
    rsi = 100 - (100 / (1 + rs))
    return rsi

data['RSI'] = calcular_rsi(data)
data['Signal_RSI'] = 0
data.loc[(data['RSI'] < 30) | (data['RSI'] > 70), 'Signal_RSI'] = 1

data['Retorno_RSI'] = data['Retorno'] * data['Signal_RSI']

retornos_rsi = data['Retorno_RSI'].dropna()
retorno_anual_rsi = retornos_rsi.mean() * 252
volatilidad_anual_rsi = retornos_rsi.std() * np.sqrt(252)
sharpe_rsi = (retorno_anual_rsi - tasa_libre_riesgo) / volatilidad_anual_rsi

print("\n[3] RSI")
print("-" * 70)
print("Retorno anualizado:", round(retorno_anual_rsi * 100, 2), "%")
print("Volatilidad anualizada:", round(volatilidad_anual_rsi * 100, 2), "%")
print("Sharpe Ratio:", round(sharpe_rsi, 3))

# RANKING FINAL
print("\n" + "="*70)
print("RANKING POR SHARPE RATIO")
print("="*70)

estrategias_sharpe = [
    ("Buy and Hold", sharpe_ratio),
    ("Medias Moviles", sharpe_ma),
    ("RSI", sharpe_rsi)
]

estrategias_sharpe_ordenadas = sorted(estrategias_sharpe, key=lambda x: x[1], reverse=True)

for i in range(len(estrategias_sharpe_ordenadas)):
    nombre = estrategias_sharpe_ordenadas[i][0]
    sharpe = estrategias_sharpe_ordenadas[i][1]
    print(str(i+1) + ". " + nombre + " - Sharpe: " + str(round(sharpe, 3)))

print("\nREFERENCIA:")
print("S&P 500 historico: ~0.4-0.5")
print("Warren Buffett: ~0.76")
print("Hedge funds top: 2.0-3.0")
print("="*70)