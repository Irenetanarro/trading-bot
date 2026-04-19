import requests
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

BASE_URL = "https://paper-api.alpaca.markets"

headers = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY
}

response = requests.get(f"{BASE_URL}/v2/clock", headers=headers)
clock = response.json()

print(f"🕐 Hora actual: {clock['timestamp']}")
print(f"📊 Mercado abierto: {'SÍ ✅' if clock['is_open'] else 'NO ❌'}")

if not clock['is_open']:
    print(f"⏰ Próxima apertura: {clock['next_open']}")
else:
    print(f"✅ ¡Mercado abierto! Puedes ejecutar el bot")