import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import os

print("\n" + "="*80)
print("DÍA 35 - TRADING AUTOMATIZADO: SETUP DE ALPACA")
print("="*80)

# Cargar API keys desde .env
load_dotenv()
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

# Alpaca Paper Trading URL
BASE_URL = "https://paper-api.alpaca.markets"

# Headers para autenticación
headers = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY
}

print("\n" + "="*80)
print("CONECTANDO A ALPACA...")
print("="*80)

# TEST 1: Verificar cuenta
print("\nTEST 1: Verificar cuenta")
print("-" * 50)

try:
    response = requests.get(f"{BASE_URL}/v2/account", headers=headers)
    
    if response.status_code == 200:
        account = response.json()
        
        print("✅ CONEXIÓN EXITOSA!")
        print(f"\nBalance de tu cuenta (paper trading):")
        print(f"  💰 Capital total: ${float(account['equity']):,.2f}")
        print(f"  💵 Cash disponible: ${float(account['cash']):,.2f}")
        print(f"  📊 Poder de compra: ${float(account['buying_power']):,.2f}")
        print(f"  📈 Posiciones abiertas: {account['position_market_value']}")
        
        print(f"\nEstado de la cuenta:")
        print(f"  Status: {account['status']}")
        print(f"  Trading bloqueado: {'No' if account['trading_blocked'] == False else 'Sí'}")
        print(f"  Cuenta: {account['account_number']}")
        
    else:
        print(f"❌ ERROR: {response.status_code}")
        print(f"Mensaje: {response.text}")
        
except Exception as e:
    print(f"❌ ERROR DE CONEXIÓN: {e}")

# TEST 2: Ver hora del mercado
print("\n" + "="*80)
print("TEST 2: Información del mercado")
print("-" * 50)

try:
    response = requests.get(f"{BASE_URL}/v2/clock", headers=headers)
    
    if response.status_code == 200:
        clock = response.json()
        
        print(f"\nEstado del mercado US:")
        print(f"  🕐 Hora actual: {clock['timestamp']}")
        print(f"  📊 Mercado abierto: {'SÍ ✅' if clock['is_open'] else 'NO ❌'}")
        
        if not clock['is_open']:
            print(f"  ⏰ Próxima apertura: {clock['next_open']}")
            print(f"  🔔 Próximo cierre: {clock['next_close']}")
            
    else:
        print(f"❌ ERROR: {response.status_code}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")

# TEST 3: Listar algunas acciones disponibles
print("\n" + "="*80)
print("TEST 3: Acciones disponibles")
print("-" * 50)

try:
    response = requests.get(f"{BASE_URL}/v2/assets/AAPL", headers=headers)
    
    if response.status_code == 200:
        asset = response.json()
        
        print(f"\nEjemplo - Apple (AAPL):")
        print(f"  Símbolo: {asset['symbol']}")
        print(f"  Nombre: {asset['name']}")
        print(f"  Exchange: {asset['exchange']}")
        print(f"  Tradeable: {'Sí ✅' if asset['tradable'] else 'No ❌'}")
        print(f"  Fracciones permitidas: {'Sí' if asset['fractionable'] else 'No'}")
        
        print("\n✅ Puedes operar con acciones US!")
        
    else:
        print(f"❌ ERROR: {response.status_code}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")

# TEST 4: Obtener precio actual
print("\n" + "="*80)
print("TEST 4: Precios en tiempo real")
print("-" * 50)

tickers = ["AAPL", "MSFT", "TSLA"]

try:
    for ticker in tickers:
        response = requests.get(
            f"{BASE_URL}/v2/stocks/{ticker}/bars/latest",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            bar = data['bar']
            
            print(f"\n{ticker}:")
            print(f"  Último precio: ${bar['c']:.2f}")
            print(f"  Volumen: {bar['v']:,}")
            print(f"  Timestamp: {bar['t']}")
        
except Exception as e:
    print(f"⚠️  No se pudieron obtener precios (mercado cerrado)")

print("\n" + "="*80)
print("DÍA 35 COMPLETADO ✅")
print("="*80)