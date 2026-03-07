import yfinance as yf

ticker = "AAPL"
data = yf.download(ticker, start="2020-01-01")

data['MA20'] = data['Close'].rolling(window=20).mean()
data['MA50'] = data['Close'].rolling(window=50).mean()

data['Signal'] = 0
data.loc[data['MA20'] > data['MA50'], 'Signal'] = 1
data['Position'] = data['Signal'].diff()

print("\nCRUCES DE MEDIAS MOVILES - AAPL")
print("="*60)

golden = len(data[data['Position'] == 1])
death = len(data[data['Position'] == -1])

print("\nGOLDEN CROSSES:", golden)
print("DEATH CROSSES:", death)

print("\nTODAS LAS SENALES:")
print("="*60)

for i in range(len(data)):
    if data['Position'].iloc[i] == 1:
        fecha = str(data.index[i])[:10]
        precio = round(data['Close'].iloc[i], 2)
        print("COMPRA -", fecha, "- Precio:", precio)
    elif data['Position'].iloc[i] == -1:
        fecha = str(data.index[i])[:10]
        precio = round(data['Close'].iloc[i], 2)
        print("VENTA  -", fecha, "- Precio:", precio)

print("\nSIMULACION:")
print("="*60)

capital = 10000
shares = 0

for i in range(len(data)):
    if data['Position'].iloc[i] == 1 and shares == 0:
        precio = data['Close'].iloc[i]
        shares = capital / precio
        fecha = str(data.index[i])[:10]
        print("COMPRA:", fecha, "Precio:", round(precio, 2), "Acciones:", round(shares, 2))
        
    elif data['Position'].iloc[i] == -1 and shares > 0:
        precio = data['Close'].iloc[i]
        capital = shares * precio
        fecha = str(data.index[i])[:10]
        print("VENTA:", fecha, "Precio:", round(precio, 2), "Capital:", round(capital, 2))
        shares = 0

if shares > 0:
    precio_final = data['Close'].iloc[-1]
    capital = shares * precio_final
    print("\nVENTA FINAL - Precio:", round(precio_final, 2), "Capital:", round(capital, 2))

print("\n" + "="*60)
print("Capital inicial: 10000")
print("Capital final:", round(capital, 2))
print("Ganancia:", round(capital - 10000, 2))
print("Porcentaje:", round(((capital/10000) - 1) * 100, 2))
print("="*60)