import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import time

print("\n" + "="*80)
print("DÍA 37 - BOT AUTOMÁTICO V1: TREND FOLLOWING")
print("="*80)

# Cargar API keys
load_dotenv()
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

BASE_URL = "https://paper-api.alpaca.markets"

headers = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY
}

# Configuración del bot
SYMBOL = "AAPL"
MA_CORTO = 20
MA_LARGO = 50
CANTIDAD = 1

print(f"\n⚙️  Configuración del Bot:")
print(f"   Símbolo: {SYMBOL}")
print(f"   MA Corta: {MA_CORTO} días")
print(f"   MA Larga: {MA_LARGO} días")
print(f"   Cantidad por operación: {CANTIDAD} acción")

# FUNCIÓN: Obtener datos históricos
def obtener_datos_historicos(symbol, days=60):
    """Obtiene precios históricos de los últimos N días"""
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    url = f"{BASE_URL}/v2/stocks/{symbol}/bars"
    params = {
        "start": start_date.strftime("%Y-%m-%d"),
        "end": end_date.strftime("%Y-%m-%d"),
        "timeframe": "1Day"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        # Verificar si la respuesta es válida
        if response.status_code != 200:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"   Mensaje: {response.text}")
            return None
        
        # Verificar si hay contenido
        if not response.text.strip():
            print(f"❌ Respuesta vacía de la API")
            return None
        
        data = response.json()
        
        if 'bars' in data and data['bars']:
            df = pd.DataFrame(data['bars'])
            df['timestamp'] = pd.to_datetime(df['t'])
            df['close'] = df['c'].astype(float)
            df = df[['timestamp', 'close']].sort_values('timestamp')
            return df
        else:
            print(f"⚠️  No hay datos en 'bars'")
            print(f"   Respuesta: {data}")
            return None
            
    except Exception as e:
        print(f"❌ Error obteniendo datos: {e}")
        return None

# FUNCIÓN: Calcular señal
def calcular_señal(df):
    """Calcula MA20, MA50 y determina señal de trading"""
    
    if len(df) < MA_LARGO:
        return None, None, None
    
    df['MA20'] = df['close'].rolling(window=MA_CORTO).mean()
    df['MA50'] = df['close'].rolling(window=MA_LARGO).mean()
    
    # Última fila
    ultimo = df.iloc[-1]
    penultimo = df.iloc[-2]
    
    ma20_actual = ultimo['MA20']
    ma50_actual = ultimo['MA50']
    ma20_anterior = penultimo['MA20']
    ma50_anterior = penultimo['MA50']
    
    # Detectar cruces
    señal = None
    
    # Golden Cross: MA20 cruza ARRIBA de MA50
    if ma20_anterior <= ma50_anterior and ma20_actual > ma50_actual:
        señal = "COMPRAR"
    
    # Death Cross: MA20 cruza ABAJO de MA50
    elif ma20_anterior >= ma50_anterior and ma20_actual < ma50_actual:
        señal = "VENDER"
    
    # Sin cruce
    else:
        if ma20_actual > ma50_actual:
            señal = "ALCISTA"
        else:
            señal = "BAJISTA"
    
    return señal, ma20_actual, ma50_actual

# FUNCIÓN: Verificar posición actual
def tengo_posicion(symbol):
    """Verifica si tenemos posición abierta en el símbolo"""
    
    try:
        response = requests.get(f"{BASE_URL}/v2/positions/{symbol}", headers=headers)
        
        if response.status_code == 200:
            pos = response.json()
            return True, int(pos['qty'])
        else:
            return False, 0
    except:
        return False, 0

# FUNCIÓN: Ejecutar orden
def ejecutar_orden(symbol, qty, side):
    """Ejecuta una orden de compra o venta"""
    
    orden = {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "type": "market",
        "time_in_force": "day"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v2/orders",
            headers=headers,
            json=orden
        )
        
        if response.status_code in [200, 201]:
            return True, response.json()
        else:
            return False, response.text
    except Exception as e:
        return False, str(e)

# PASO 1: Verificar mercado
print("\n" + "="*80)
print("PASO 1: Verificar estado del mercado")
print("="*80)

response = requests.get(f"{BASE_URL}/v2/clock", headers=headers)
clock = response.json()

print(f"\n🕐 Hora actual: {clock['timestamp']}")
print(f"📊 Mercado abierto: {'SÍ ✅' if clock['is_open'] else 'NO ❌'}")

if not clock['is_open']:
    print(f"\n⚠️  El mercado está cerrado")
    print(f"⏰ Próxima apertura: {clock['next_open']}")
    print(f"\n💡 El bot puede analizar señales pero no ejecutar órdenes")

# PASO 2: Ver balance y posición actual
print("\n" + "="*80)
print("PASO 2: Estado de tu cuenta")
print("="*80)

response = requests.get(f"{BASE_URL}/v2/account", headers=headers)
account = response.json()

print(f"\n💰 Cash disponible: ${float(account['cash']):,.2f}")
print(f"📊 Equity total: ${float(account['equity']):,.2f}")

tiene_posicion, cantidad_actual = tengo_posicion(SYMBOL)

if tiene_posicion:
    print(f"\n📈 Posición actual: {cantidad_actual} {SYMBOL}")
else:
    print(f"\n📭 No tienes posición en {SYMBOL}")

# PASO 3: Obtener datos históricos
print("\n" + "="*80)
print("PASO 3: Obtener datos históricos")
print("="*80)

print(f"\n🔄 Descargando últimos 60 días de {SYMBOL}...")

df = obtener_datos_historicos(SYMBOL, days=60)

if df is None or len(df) < MA_LARGO:
    print(f"\n❌ No se pudieron obtener suficientes datos históricos")
    print(f"\n💡 Esto puede pasar si:")
    print(f"   1. El mercado está cerrado y los datos no están disponibles")
    print(f"   2. Hay un problema temporal con la API")
    print(f"   3. El símbolo no es válido")
    print(f"\n🔄 Soluciones:")
    print(f"   1. Ejecutar cuando el mercado esté abierto (3:30pm-10pm España)")
    print(f"   2. Intentar más tarde")
    print(f"   3. Verificar que {SYMBOL} es un símbolo válido")
    print(f"\n✅ El bot funcionaría correctamente con datos válidos")
    print(f"   Mañana continuaremos con Risk Management automático")
    exit()

print(f"✅ Datos obtenidos: {len(df)} días")
print(f"\n📅 Rango de datos:")
print(f"   Inicio: {df['timestamp'].min()}")
print(f"   Fin: {df['timestamp'].max()}")
print(f"\n💵 Último precio: ${df['close'].iloc[-1]:.2f}")

# PASO 4: Calcular señal
print("\n" + "="*80)
print("PASO 4: Calcular señal de trading")
print("="*80)

señal, ma20, ma50 = calcular_señal(df)

print(f"\n📊 Medias móviles:")
print(f"   MA20: ${ma20:.2f}")
print(f"   MA50: ${ma50:.2f}")

print(f"\n🎯 Señal detectada: {señal}")

if señal == "COMPRAR":
    print(f"   🟢 GOLDEN CROSS detectado!")
    print(f"   ➡️  MA20 cruzó ARRIBA de MA50")
    print(f"   📈 Tendencia ALCISTA")
elif señal == "VENDER":
    print(f"   🔴 DEATH CROSS detectado!")
    print(f"   ➡️  MA20 cruzó ABAJO de MA50")
    print(f"   📉 Tendencia BAJISTA")
elif señal == "ALCISTA":
    print(f"   📊 Tendencia alcista (MA20 > MA50)")
    print(f"   ⏸️  Sin cruce reciente - sin acción")
else:
    print(f"   📊 Tendencia bajista (MA20 < MA50)")
    print(f"   ⏸️  Sin cruce reciente - sin acción")

# PASO 5: Decidir acción
print("\n" + "="*80)
print("PASO 5: Decisión del bot")
print("="*80)

accion = None

if señal == "COMPRAR" and not tiene_posicion:
    accion = "COMPRAR"
    print(f"\n🤖 Bot decide: COMPRAR {CANTIDAD} {SYMBOL}")
    print(f"   Razón: Golden cross + No tengo posición")
    
elif señal == "VENDER" and tiene_posicion:
    accion = "VENDER"
    print(f"\n🤖 Bot decide: VENDER {cantidad_actual} {SYMBOL}")
    print(f"   Razón: Death cross + Tengo posición")
    
elif señal == "COMPRAR" and tiene_posicion:
    print(f"\n⏸️  Bot decide: NO HACER NADA")
    print(f"   Razón: Golden cross pero ya tengo posición")
    
elif señal == "VENDER" and not tiene_posicion:
    print(f"\n⏸️  Bot decide: NO HACER NADA")
    print(f"   Razón: Death cross pero no tengo posición")
    
else:
    print(f"\n⏸️  Bot decide: NO HACER NADA")
    print(f"   Razón: Sin señal de cruce")

# PASO 6: Ejecutar acción
if accion and clock['is_open']:
    print("\n" + "="*80)
    print("PASO 6: Ejecutar orden")
    print("="*80)
    
    print(f"\n🚀 Ejecutando {accion}...")
    
    side = "buy" if accion == "COMPRAR" else "sell"
    qty = CANTIDAD if accion == "COMPRAR" else cantidad_actual
    
    exito, resultado = ejecutar_orden(SYMBOL, qty, side)
    
    if exito:
        print(f"\n✅ ¡ORDEN EJECUTADA!")
        print(f"   Order ID: {resultado['id']}")
        print(f"   Symbol: {resultado['symbol']}")
        print(f"   Side: {resultado['side'].upper()}")
        print(f"   Qty: {resultado['qty']}")
        print(f"   Status: {resultado['status']}")
        
        print(f"\n⏳ Esperando confirmación...")
        
        for i in range(10):
            time.sleep(2)
            
            response = requests.get(
                f"{BASE_URL}/v2/orders/{resultado['id']}",
                headers=headers
            )
            orden_status = response.json()
            
            if orden_status['status'] == 'filled':
                precio = float(orden_status['filled_avg_price'])
                print(f"\n✅ ¡EJECUTADA!")
                print(f"   Precio: ${precio:.2f}")
                print(f"   Cantidad: {orden_status['filled_qty']}")
                break
            else:
                print(f"   Status: {orden_status['status']}")
    else:
        print(f"\n❌ ERROR al ejecutar orden:")
        print(f"   {resultado}")
        
elif accion and not clock['is_open']:
    print("\n⚠️  Mercado cerrado - No se puede ejecutar la orden")
    print(f"   El bot detectó {accion} pero el mercado está cerrado")

# PASO 7: Estado final
print("\n" + "="*80)
print("PASO 7: Estado final")
print("="*80)

time.sleep(1)

response = requests.get(f"{BASE_URL}/v2/account", headers=headers)
account = response.json()

print(f"\n💰 Cash: ${float(account['cash']):,.2f}")
print(f"📊 Equity: ${float(account['equity']):,.2f}")

tiene_posicion_final, cantidad_final = tengo_posicion(SYMBOL)

if tiene_posicion_final:
    response = requests.get(f"{BASE_URL}/v2/positions/{SYMBOL}", headers=headers)
    pos = response.json()
    
    print(f"\n📈 Posición en {SYMBOL}:")
    print(f"   Cantidad: {pos['qty']}")
    print(f"   Precio promedio: ${float(pos['avg_entry_price']):.2f}")
    print(f"   Precio actual: ${float(pos['current_price']):.2f}")
    print(f"   Ganancia/Pérdida: ${float(pos['unrealized_pl']):.2f}")
else:
    print(f"\n📭 Sin posiciones abiertas")

print("\n" + "="*80)
print("DÍA 37 COMPLETADO ✅")
print("="*80)