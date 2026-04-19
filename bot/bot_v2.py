import requests
from dotenv import load_dotenv
import os
import time

print("\n" + "="*80)
print("DÍA 38 - BOT V2: RISK MANAGEMENT AUTOMÁTICO")
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

# CONFIGURACIÓN DE RISK MANAGEMENT
SYMBOL = "AAPL"
KELLY_FRACTION = 0.122  # Half Kelly = 12.2%
STOP_LOSS_PCT = 0.10    # -10%
TAKE_PROFIT_PCT = 0.20  # +20%

print(f"\n⚙️  Configuración del Bot v2:")
print(f"   Símbolo: {SYMBOL}")
print(f"   Half Kelly: {KELLY_FRACTION*100:.1f}% del capital")
print(f"   Stop Loss: -{STOP_LOSS_PCT*100:.0f}%")
print(f"   Take Profit: +{TAKE_PROFIT_PCT*100:.0f}%")

# FUNCIÓN: Calcular tamaño de posición con Kelly
def calcular_tamaño_kelly(capital_total, precio_accion, kelly_fraction=0.122):
    """Calcula cuántas acciones comprar basado en Half Kelly"""
    
    capital_para_operacion = capital_total * kelly_fraction
    cantidad = int(capital_para_operacion / precio_accion)
    
    if cantidad < 1:
        cantidad = 1
    
    return cantidad, capital_para_operacion

# FUNCIÓN: Verificar posición actual
def obtener_posicion(symbol):
    """Obtiene detalles de la posición actual"""
    
    try:
        response = requests.get(f"{BASE_URL}/v2/positions/{symbol}", headers=headers)
        
        if response.status_code == 200:
            pos = response.json()
            return {
                'tiene_posicion': True,
                'cantidad': int(pos['qty']),
                'precio_entrada': float(pos['avg_entry_price']),
                'precio_actual': float(pos['current_price']),
                'ganancia': float(pos['unrealized_pl']),
                'ganancia_pct': float(pos['unrealized_plpc']) * 100
            }
        else:
            return {'tiene_posicion': False}
    except:
        return {'tiene_posicion': False}

# FUNCIÓN: Verificar si debe activar Stop Loss
def debe_activar_stop_loss(posicion, stop_loss_pct):
    """Verifica si la pérdida alcanzó el Stop Loss"""
    
    if not posicion['tiene_posicion']:
        return False
    
    perdida_pct = posicion['ganancia_pct']
    
    if perdida_pct <= -stop_loss_pct * 100:
        return True
    
    return False

# FUNCIÓN: Verificar si debe activar Take Profit
def debe_activar_take_profit(posicion, take_profit_pct):
    """Verifica si la ganancia alcanzó el Take Profit"""
    
    if not posicion['tiene_posicion']:
        return False
    
    ganancia_pct = posicion['ganancia_pct']
    
    if ganancia_pct >= take_profit_pct * 100:
        return True
    
    return False

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

# FUNCIÓN: Obtener precio actual
def obtener_precio_actual(symbol):
    """Obtiene el último precio conocido"""
    
    try:
        pos = obtener_posicion(symbol)
        if pos['tiene_posicion']:
            return pos['precio_actual']
        
        response = requests.get(
            f"{BASE_URL}/v2/stocks/{symbol}/trades/latest",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'trade' in data:
                return float(data['trade']['p'])
        
        return 260.0
        
    except:
        return 260.0

# PASO 1: Verificar mercado
print("\n" + "="*80)
print("PASO 1: Verificar estado del mercado")
print("="*80)

response = requests.get(f"{BASE_URL}/v2/clock", headers=headers)
clock = response.json()

print(f"\n🕐 Hora actual: {clock['timestamp']}")
print(f"📊 Mercado abierto: {'SÍ ✅' if clock['is_open'] else 'NO ❌'}")

# PASO 2: Ver balance
print("\n" + "="*80)
print("PASO 2: Balance de tu cuenta")
print("="*80)

response = requests.get(f"{BASE_URL}/v2/account", headers=headers)
account = response.json()

capital_total = float(account['equity'])
cash = float(account['cash'])

print(f"\n💰 Cash disponible: ${cash:,.2f}")
print(f"📊 Equity total: ${capital_total:,.2f}")

# PASO 3: Ver posición actual
print("\n" + "="*80)
print("PASO 3: Posición actual")
print("="*80)

posicion = obtener_posicion(SYMBOL)

if posicion['tiene_posicion']:
    print(f"\n📈 Tienes posición en {SYMBOL}:")
    print(f"   Cantidad: {posicion['cantidad']}")
    print(f"   Precio entrada: ${posicion['precio_entrada']:.2f}")
    print(f"   Precio actual: ${posicion['precio_actual']:.2f}")
    print(f"   Ganancia/Pérdida: ${posicion['ganancia']:.2f} ({posicion['ganancia_pct']:+.2f}%)")
else:
    print(f"\n📭 No tienes posición en {SYMBOL}")

# PASO 4: Verificar Stop Loss
print("\n" + "="*80)
print("PASO 4: Verificar Stop Loss")
print("="*80)

if posicion['tiene_posicion']:
    activar_sl = debe_activar_stop_loss(posicion, STOP_LOSS_PCT)
    
    precio_sl = posicion['precio_entrada'] * (1 - STOP_LOSS_PCT)
    
    print(f"\n🛡️  Stop Loss configurado:")
    print(f"   Nivel: ${precio_sl:.2f} (-10% desde ${posicion['precio_entrada']:.2f})")
    print(f"   Precio actual: ${posicion['precio_actual']:.2f}")
    
    if activar_sl:
        print(f"\n🚨 ¡STOP LOSS ACTIVADO!")
        print(f"   Pérdida actual: {posicion['ganancia_pct']:.2f}%")
        print(f"   Acción: VENDER para proteger capital")
    else:
        distancia_sl = ((posicion['precio_actual'] - precio_sl) / precio_sl) * 100
        print(f"\n✅ Stop Loss NO activado")
        print(f"   Distancia: {distancia_sl:.2f}% por encima del SL")
else:
    print(f"\n⏸️  Sin posición - Stop Loss no aplica")

# PASO 5: Verificar Take Profit
print("\n" + "="*80)
print("PASO 5: Verificar Take Profit")
print("="*80)

if posicion['tiene_posicion']:
    activar_tp = debe_activar_take_profit(posicion, TAKE_PROFIT_PCT)
    
    precio_tp = posicion['precio_entrada'] * (1 + TAKE_PROFIT_PCT)
    
    print(f"\n🎯 Take Profit configurado:")
    print(f"   Nivel: ${precio_tp:.2f} (+20% desde ${posicion['precio_entrada']:.2f})")
    print(f"   Precio actual: ${posicion['precio_actual']:.2f}")
    
    if activar_tp:
        print(f"\n🎉 ¡TAKE PROFIT ACTIVADO!")
        print(f"   Ganancia actual: {posicion['ganancia_pct']:.2f}%")
        print(f"   Acción: VENDER para asegurar ganancias")
    else:
        distancia_tp = ((precio_tp - posicion['precio_actual']) / posicion['precio_actual']) * 100
        print(f"\n⏳ Take Profit NO alcanzado")
        print(f"   Falta: {distancia_tp:.2f}% para alcanzar el TP")
else:
    print(f"\n⏸️  Sin posición - Take Profit no aplica")

# PASO 6: Calcular tamaño de posición con Kelly
print("\n" + "="*80)
print("PASO 6: Tamaño de posición con Half Kelly")
print("="*80)

if not posicion['tiene_posicion']:
    precio_actual = obtener_precio_actual(SYMBOL)
    
    cantidad_kelly, capital_operacion = calcular_tamaño_kelly(
        capital_total, 
        precio_actual, 
        KELLY_FRACTION
    )
    
    print(f"\n📊 Cálculo de Kelly:")
    print(f"   Capital total: ${capital_total:,.2f}")
    print(f"   Half Kelly: {KELLY_FRACTION*100:.1f}%")
    print(f"   Capital para operación: ${capital_operacion:,.2f}")
    print(f"   Precio de {SYMBOL}: ${precio_actual:.2f}")
    print(f"   Cantidad a comprar: {cantidad_kelly} acciones")
    print(f"   Costo total: ${cantidad_kelly * precio_actual:.2f}")
    
    print(f"\n💡 Comparación:")
    print(f"   All-in (100%): {int(capital_total / precio_actual)} acciones")
    print(f"   Half Kelly (12.2%): {cantidad_kelly} acciones ✅")
else:
    print(f"\n⏸️  Ya tienes posición - Kelly no aplica ahora")

# PASO 7: Decisión del bot
print("\n" + "="*80)
print("PASO 7: Decisión del bot con Risk Management")
print("="*80)

accion = None
razon = ""

if posicion['tiene_posicion']:
    if activar_sl:
        accion = "VENDER"
        razon = f"Stop Loss activado ({posicion['ganancia_pct']:.2f}%)"
    elif activar_tp:
        accion = "VENDER"
        razon = f"Take Profit activado ({posicion['ganancia_pct']:.2f}%)"
    else:
        accion = "MANTENER"
        razon = f"Dentro del rango (SL: -{STOP_LOSS_PCT*100}%, TP: +{TAKE_PROFIT_PCT*100}%)"
else:
    accion = "ESPERAR"
    razon = "Sin posición y sin señal de compra"

print(f"\n🤖 Bot decide: {accion}")
print(f"   Razón: {razon}")

# PASO 8: Ejecutar acción
if accion == "VENDER" and clock['is_open']:
    print("\n" + "="*80)
    print("PASO 8: Ejecutar orden de VENTA")
    print("="*80)
    
    print(f"\n🚀 Vendiendo {posicion['cantidad']} {SYMBOL}...")
    
    exito, resultado = ejecutar_orden(SYMBOL, posicion['cantidad'], "sell")
    
    if exito:
        print(f"\n✅ ¡ORDEN ENVIADA!")
        print(f"   Order ID: {resultado['id']}")
        print(f"   Status: {resultado['status']}")
        
        print(f"\n⏳ Esperando ejecución...")
        
        for i in range(10):
            time.sleep(2)
            
            response = requests.get(
                f"{BASE_URL}/v2/orders/{resultado['id']}",
                headers=headers
            )
            orden_status = response.json()
            
            print(f"   Status: {orden_status['status']}")
            
            if orden_status['status'] == 'filled':
                precio = float(orden_status['filled_avg_price'])
                print(f"\n✅ ¡VENTA EJECUTADA!")
                print(f"   Precio: ${precio:.2f}")
                break
    else:
        print(f"\n❌ ERROR: {resultado}")

# PASO 9: Estado final
print("\n" + "="*80)
print("PASO 9: Estado final")
print("="*80)

time.sleep(1)

response = requests.get(f"{BASE_URL}/v2/account", headers=headers)
account = response.json()

print(f"\n💰 Cash: ${float(account['cash']):,.2f}")
print(f"📊 Equity: ${float(account['equity']):,.2f}")

posicion_final = obtener_posicion(SYMBOL)

if posicion_final['tiene_posicion']:
    print(f"\n📈 Posición en {SYMBOL}:")
    print(f"   Cantidad: {posicion_final['cantidad']}")
    print(f"   Precio entrada: ${posicion_final['precio_entrada']:.2f}")
    print(f"   Precio actual: ${posicion_final['precio_actual']:.2f}")
    print(f"   G/P: ${posicion_final['ganancia']:.2f} ({posicion_final['ganancia_pct']:+.2f}%)")
    
    sl = posicion_final['precio_entrada'] * (1 - STOP_LOSS_PCT)
    tp = posicion_final['precio_entrada'] * (1 + TAKE_PROFIT_PCT)
    
    print(f"\n🛡️  Protecciones activas:")
    print(f"   Stop Loss: ${sl:.2f} (-10%)")
    print(f"   Take Profit: ${tp:.2f} (+20%)")
else:
    print(f"\n📭 Sin posiciones")

print("\n" + "="*80)
print("DÍA 38 COMPLETADO ✅")
print("="*80)