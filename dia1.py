import yfinance as yf

# Descargar datos de varias empresas
tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

for ticker in tickers:
    data = yf.download(ticker, start="2020-01-01")
    print(f"\n--- {ticker} ---")
    print(data.tail(5))