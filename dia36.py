import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import os
import time

print("\n" + "="*80)
print("DÍA 36 - TU PRIMERA ORDEN PROGRAMÁTICA")
print("="*80)

# Cargar API keys desde .env
load_dotenv()
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

BASE_URL = "https://paper-api.alpaca.markets"

headers = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY
}

# VERIFICAR SI EL MERCADO ESTÁ ABIERTO
print("\n" + "="*80)
print("VERIFICANDO ESTADO DEL MERCADO")
print("="*80)

response = requests.get(f"{BASE_URL}/v2/clock", headers=headers)
clock = response.json()

print(f"\n🕐 Hora actual: {clock['timestamp']}")
print(f"📊 Mercado abierto: {'SÍ ✅' if clock['is_open'] else 'NO ❌'}")

if not clock['is_open']:
    print(f"\n⚠️  El mercado está CERRADO")
    print(f"⏰ Próxima apertura: {clock['next_open']}")
    print(f"\n💡 Para ejecutar este código:")
    print(f"   1. Espera a que el mercado abra (3:30pm - 10pm hora España)")
    print(f"   2. O modifica el código para usar 'gtc' (good til cancelled)")
    print(f"\nPor ahora, usaremos una orden GTC que se ejecutará cuando abra el mercado.")
    time_in_force = "gtc"
else:
    print(f"\n✅ Mercado abierto, procediendo...")
    time_in_force = "day"

# PASO 1: Ver balance inicial
print("\n" + "="*80)
print("PASO 1: Balance inicial")
print("="*80)

response = requests.get(f"{BASE_URL}/v2/account", headers=headers)
account = response.json()

balance_inicial = float(account['cash'])
print(f"\n💰 Cash disponible: ${balance_inicial:,.2f}")
print(f"📊 Posiciones abiertas: {account['position_market_value']}")

# PASO 2: Ver precio más reciente de AAPL
print("\n" + "="*80)
print("PASO 2: Último precio conocido de AAPL")
print("="*80)

try:
    response = requests.get(f"{BASE_URL}/v2/stocks/AAPL/bars/latest", headers=headers)
    
    # Verificar si la respuesta es válida
    if response.status_code == 200 and response.text.strip():
        data = response.json()
        if 'bar' in data and data['bar']:
            precio_aapl = data['bar']['c']
            print(f"\n📈 AAPL último precio: ${precio_aapl:.2f}")
        else:
            print(f"\n⚠️  No hay precio reciente disponible")
            print(f"   Usando orden market (se ejecutará al mejor precio disponible)")
            precio_aapl = None
    else:
        print(f"\n⚠️  No se pudo obtener precio (mercado cerrado)")
        print(f"   Usando orden market (se ejecutará cuando abra)")
        precio_aapl = None
        
except Exception as e:
    print(f"\n⚠️  Error obteniendo precio: {e}")
    print(f"   Usando orden market")
    precio_aapl = None

# PASO 3: Comprar 1 acción de AAPL
print("\n" + "="*80)
print("PASO 3: Comprar 1 acción de AAPL")
print("="*80)

orden_compra = {
    "symbol": "AAPL",
    "qty": 1,
    "side": "buy",
    "type": "market",
    "time_in_force": time_in_force
}

print("\n🔄 Enviando orden de COMPRA...")
print(f"   Símbolo: AAPL")
print(f"   Cantidad: 1 acción")
print(f"   Tipo: Market")
print(f"   Time in force: {time_in_force}")

response = requests.post(
    f"{BASE_URL}/v2/orders",
    headers=headers,
    json=orden_compra
)

if response.status_code in [200, 201]:
    orden = response.json()
    order_id = orden['id']
    
    print("\n✅ ¡ORDEN DE COMPRA ENVIADA!")
    print(f"   Order ID: {order_id}")
    print(f"   Status: {orden['status']}")
    
    if orden['status'] == 'pending_new' or orden['status'] == 'accepted':
        print(f"\n⏳ Orden aceptada, esperará a que el mercado abra para ejecutarse")
        print(f"\n💡 Puedes verificar el estado después con:")
        print(f"   GET {BASE_URL}/v2/orders/{order_id}")
        print(f"\n✅ Día 36 completado - Orden creada exitosamente")
        print(f"   La orden se ejecutará cuando el mercado abra")
        exit()
    
    # Si el mercado está abierto, esperar ejecución
    print("\n⏳ Esperando ejecución...")
    
    for i in range(15):
        time.sleep(2)
        
        response = requests.get(f"{BASE_URL}/v2/orders/{order_id}", headers=headers)
        orden_status = response.json()
        
        print(f"   Status: {orden_status['status']}")
        
        if orden_status['status'] == 'filled':
            precio_ejecucion = float(orden_status['filled_avg_price'])
            print(f"\n✅ ¡COMPRA EJECUTADA!")
            print(f"   Precio de ejecución: ${precio_ejecucion:.2f}")
            print(f"   Cantidad: {orden_status['filled_qty']} acción")
            print(f"   Costo total: ${precio_ejecucion:.2f}")
            precio_compra = precio_ejecucion
            break
        elif orden_status['status'] in ['pending_new', 'accepted', 'new']:
            continue
        else:
            print(f"\n⚠️  Status inesperado: {orden_status['status']}")
            break
    else:
        print(f"\n⏰ Timeout esperando ejecución")
        print(f"   La orden está en estado: {orden_status['status']}")
        if orden_status['status'] in ['pending_new', 'accepted', 'new']:
            print(f"   Se ejecutará cuando el mercado abra")
        exit()
    
else:
    print(f"\n❌ ERROR: {response.status_code}")
    print(f"Mensaje: {response.text}")
    exit()

# PASO 4: Ver posición abierta
print("\n" + "="*80)
print("PASO 4: Ver tu posición abierta")
print("="*80)

time.sleep(2)

response = requests.get(f"{BASE_URL}/v2/positions/AAPL", headers=headers)

if response.status_code == 200:
    pos = response.json()
    
    print(f"\n📊 Posición en AAPL:")
    print(f"   Cantidad: {pos['qty']} acción")
    print(f"   Precio promedio: ${float(pos['avg_entry_price']):.2f}")
    print(f"   Precio actual: ${float(pos['current_price']):.2f}")
    print(f"   Valor de mercado: ${float(pos['market_value']):.2f}")
    print(f"   Ganancia/Pérdida: ${float(pos['unrealized_pl']):.2f} ({float(pos['unrealized_plpc'])*100:.2f}%)")
    
    precio_compra = float(pos['avg_entry_price'])
else:
    print(f"\n⚠️  No se pudo obtener la posición")

# PASO 5: Ver balance después de compra
print("\n" + "="*80)
print("PASO 5: Balance después de compra")
print("="*80)

response = requests.get(f"{BASE_URL}/v2/account", headers=headers)
account = response.json()

balance_despues_compra = float(account['cash'])
equity = float(account['equity'])

print(f"\n💰 Cash disponible: ${balance_despues_compra:,.2f}")
print(f"📊 Valor total (equity): ${equity:,.2f}")
print(f"💸 Gastado en compra: ${balance_inicial - balance_despues_compra:.2f}")

# PASO 6: Esperar y ver cambios
print("\n" + "="*80)
print("PASO 6: Monitoreando precio (10 segundos)...")
print("="*80)

for i in range(10, 0, -1):
    print(f"⏳ {i} segundos...", end='\r')
    time.sleep(1)

print("\n")

# Ver precio actualizado
response = requests.get(f"{BASE_URL}/v2/positions/AAPL", headers=headers)

if response.status_code == 200:
    pos = response.json()
    
    precio_actual = float(pos['current_price'])
    ganancia = float(pos['unrealized_pl'])
    ganancia_pct = float(pos['unrealized_plpc']) * 100
    
    print(f"📈 Precio actual: ${precio_actual:.2f}")
    print(f"💵 Compraste a: ${precio_compra:.2f}")
    print(f"{'📈' if ganancia >= 0 else '📉'} Ganancia/Pérdida: ${ganancia:.2f} ({ganancia_pct:+.2f}%)")

# PASO 7: Vender la acción
print("\n" + "="*80)
print("PASO 7: Vender 1 acción de AAPL")
print("="*80)

input("\n⏸️  Presiona ENTER para vender la acción...")

orden_venta = {
    "symbol": "AAPL",
    "qty": 1,
    "side": "sell",
    "type": "market",
    "time_in_force": time_in_force
}

print("\n🔄 Enviando orden de VENTA...")

response = requests.post(
    f"{BASE_URL}/v2/orders",
    headers=headers,
    json=orden_venta
)

if response.status_code in [200, 201]:
    orden = response.json()
    order_id_venta = orden['id']
    
    print("\n✅ ¡ORDEN DE VENTA ENVIADA!")
    print(f"   Order ID: {order_id_venta}")
    print(f"   Status: {orden['status']}")
    
    # Esperar ejecución
    print("\n⏳ Esperando ejecución...")
    
    for i in range(15):
        time.sleep(2)
        
        response = requests.get(f"{BASE_URL}/v2/orders/{order_id_venta}", headers=headers)
        orden_status = response.json()
        
        print(f"   Status: {orden_status['status']}")
        
        if orden_status['status'] == 'filled':
            precio_venta = float(orden_status['filled_avg_price'])
            print(f"\n✅ ¡VENTA EJECUTADA!")
            print(f"   Precio de venta: ${precio_venta:.2f}")
            break
        elif orden_status['status'] in ['pending_new', 'accepted', 'new']:
            continue
        else:
            break
else:
    print(f"\n❌ ERROR: {response.status_code}")
    print(f"Mensaje: {response.text}")

# PASO 8: Balance final
print("\n" + "="*80)
print("PASO 8: Resultado final")
print("="*80)

time.sleep(2)

response = requests.get(f"{BASE_URL}/v2/account", headers=headers)
account = response.json()

balance_final = float(account['cash'])
ganancia_total = balance_final - balance_inicial

print(f"\n💰 Balance inicial: ${balance_inicial:,.2f}")
print(f"💰 Balance final: ${balance_final:,.2f}")
print(f"\n{'🎉' if ganancia_total >= 0 else '😢'} Ganancia/Pérdida: ${ganancia_total:+.2f}")

print("\n" + "="*80)
print("DÍA 36 COMPLETADO ✅")
print("="*80)