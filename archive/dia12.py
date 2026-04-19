import yfinance as yf

ticker = "AAPL"
data = yf.download(ticker, start="2020-01-01")

# Calcular medias móviles
data['MA20'] = data['Close'].rolling(window=20).mean()
data['MA50'] = data['Close'].rolling(window=50).mean()

print("\n" + "="*70)
print("COMPARACION DE 3 ESTRATEGIAS - APPLE (2020-2026)")
print("="*70)

# ESTRATEGIA 1: MEDIAS MOVILES
print("\n[1] ESTRATEGIA: MEDIAS MOVILES (Golden Cross)")
print("-" * 70)

data['Signal_MA'] = 0
data.loc[data['MA20'] > data['MA50'], 'Signal_MA'] = 1
data['Position_MA'] = data['Signal_MA'].diff()

capital_ma = 10000.0
shares_ma = 0.0
operaciones_ma = 0

for i in range(len(data)):
    pos = data['Position_MA'].values[i]
    
    if pos == 1.0 and shares_ma == 0.0:
        precio = data['Close'].values[i]
        shares_ma = capital_ma / precio
        operaciones_ma = operaciones_ma + 1
    elif pos == -1.0 and shares_ma > 0.0:
        precio = data['Close'].values[i]
        capital_ma = shares_ma * precio
        shares_ma = 0.0
        operaciones_ma = operaciones_ma + 1

if shares_ma > 0.0:
    precio_final = data['Close'].values[-1]
    capital_ma = shares_ma * precio_final

# Convertir a escalar si es necesario
if hasattr(capital_ma, 'item'):
    capital_ma = capital_ma.item()

ganancia_ma = capital_ma - 10000
pct_ma = ((capital_ma / 10000) - 1) * 100

print("Capital final:", int(capital_ma))
print("Ganancia:", int(ganancia_ma))
print("Porcentaje:", int(pct_ma), "%")
print("Operaciones:", operaciones_ma)

# Calcular RSI
def calcular_rsi(data, periodo=14):
    delta = data['Close'].diff()
    ganancias = delta.where(delta > 0, 0)
    perdidas = -delta.where(delta < 0, 0)
    avg_ganancias = ganancias.rolling(window=periodo).mean()
    avg_perdidas = perdidas.rolling(window=periodo).mean()
    rs = avg_ganancias / avg_perdidas
    rsi = 100 - (100 / (1 + rs))
    return rsi

data['RSI'] = calcular_rsi(data, periodo=14)

# ESTRATEGIA 2: RSI
print("\n[2] ESTRATEGIA: RSI (Comprar en sobreventa < 30)")
print("-" * 70)

capital_rsi = 10000.0
shares_rsi = 0.0
operaciones_rsi = 0

for i in range(len(data)):
    rsi = data['RSI'].values[i]
    
    if rsi < 30 and shares_rsi == 0.0:
        precio = data['Close'].values[i]
        shares_rsi = capital_rsi / precio
        operaciones_rsi = operaciones_rsi + 1
    elif rsi > 70 and shares_rsi > 0.0:
        precio = data['Close'].values[i]
        capital_rsi = shares_rsi * precio
        shares_rsi = 0.0
        operaciones_rsi = operaciones_rsi + 1

if shares_rsi > 0.0:
    precio_final = data['Close'].values[-1]
    capital_rsi = shares_rsi * precio_final

if hasattr(capital_rsi, 'item'):
    capital_rsi = capital_rsi.item()

ganancia_rsi = capital_rsi - 10000
pct_rsi = ((capital_rsi / 10000) - 1) * 100

print("Capital final:", int(capital_rsi))
print("Ganancia:", int(ganancia_rsi))
print("Porcentaje:", int(pct_rsi), "%")
print("Operaciones:", operaciones_rsi)

# Calcular Bandas de Bollinger
data['STD'] = data['Close'].rolling(window=20).std()
data['BB_Superior'] = data['MA20'] + (2 * data['STD'])
data['BB_Inferior'] = data['MA20'] - (2 * data['STD'])

# ESTRATEGIA 3: BANDAS DE BOLLINGER
print("\n[3] ESTRATEGIA: BANDAS DE BOLLINGER (Comprar en banda inferior)")
print("-" * 70)

capital_bb = 10000.0
shares_bb = 0.0
operaciones_bb = 0

for i in range(len(data)):
    precio = data['Close'].values[i]
    bb_inf = data['BB_Inferior'].values[i]
    bb_sup = data['BB_Superior'].values[i]
    
    if precio <= bb_inf and shares_bb == 0.0:
        shares_bb = capital_bb / precio
        operaciones_bb = operaciones_bb + 1
    elif precio >= bb_sup and shares_bb > 0.0:
        capital_bb = shares_bb * precio
        shares_bb = 0.0
        operaciones_bb = operaciones_bb + 1

if shares_bb > 0.0:
    precio_final = data['Close'].values[-1]
    capital_bb = shares_bb * precio_final

if hasattr(capital_bb, 'item'):
    capital_bb = capital_bb.item()

ganancia_bb = capital_bb - 10000
pct_bb = ((capital_bb / 10000) - 1) * 100

print("Capital final:", int(capital_bb))
print("Ganancia:", int(ganancia_bb))
print("Porcentaje:", int(pct_bb), "%")
print("Operaciones:", operaciones_bb)

# BUY AND HOLD (referencia)
print("\n[REFERENCIA] BUY AND HOLD (Comprar y no hacer nada)")
print("-" * 70)

precio_inicial = data['Close'].values[0]
precio_final = data['Close'].values[-1]
capital_bh = 10000 * (precio_final / precio_inicial)

if hasattr(capital_bh, 'item'):
    capital_bh = capital_bh.item()

ganancia_bh = capital_bh - 10000
pct_bh = ((capital_bh / 10000) - 1) * 100

print("Capital final:", int(capital_bh))
print("Ganancia:", int(ganancia_bh))
print("Porcentaje:", int(pct_bh), "%")
print("Operaciones: 1 (solo compra inicial)")

# RESUMEN COMPARATIVO
print("\n" + "="*70)
print("RANKING DE ESTRATEGIAS")
print("="*70)

estrategias = [
    ("Buy and Hold", capital_bh, pct_bh, 1),
    ("Medias Moviles", capital_ma, pct_ma, operaciones_ma),
    ("RSI", capital_rsi, pct_rsi, operaciones_rsi),
    ("Bandas Bollinger", capital_bb, pct_bb, operaciones_bb)
]

estrategias_ordenadas = sorted(estrategias, key=lambda x: x[1], reverse=True)

for i in range(len(estrategias_ordenadas)):
    nombre = estrategias_ordenadas[i][0]
    capital = estrategias_ordenadas[i][1]
    pct = estrategias_ordenadas[i][2]
    ops = estrategias_ordenadas[i][3]
    print(str(i+1) + ". " + nombre + " - Capital: $" + str(int(capital)) + " - " + str(int(pct)) + "% - Ops: " + str(ops))

print("="*70)