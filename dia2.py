import yfinance as yf
import pandas as pd

# Descargar datos de Apple
aapl = yf.download("AAPL", start="2020-01-01")

# Calcular retornos diarios (cambio porcentual día a día)
aapl['Returns'] = aapl['Close'].pct_change()

# Mostrar precio y retornos
print(aapl[['Close', 'Returns']].tail(10))

# Calcular retorno promedio diario
print(f"\nRetorno promedio diario: {aapl['Returns'].mean():.4f}")
print(f"Retorno promedio diario (%): {aapl['Returns'].mean() * 100:.2f}%")