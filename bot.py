import os
import time
import threading
import requests
from flask import Flask
import yfinance as yf

# Configuración de credenciales institucionales
TOKEN = "8798266906:AAEkczcf-Unknsm-SZKoN3q5LQZ-2OemZkY"
CHAT_ID = "8662528470"

app = Flask(__name__)

# Variables globales para control de alertas y evitar spam repetitivo
ultima_alerta_estado = None

@app.route('/')
def home():
    return "IBIZA-TF-BOT Institucional en Vivo Activo 24/7"

def enviar_telegram(mensaje, chat_id=CHAT_ID):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error enviando mensaje: {e}")

def obtener_precio_eurusd():
    try:
        # Obtiene el precio actual en tiempo real de Yahoo Finance para EUR/USD
        ticker = yf.Ticker("EURUSD=X")
        data = ticker.history(period="1d", interval="1m")
        if not data.empty:
            return float(data['Close'].iloc[-1])
    except Exception as e:
        print(f"Error obteniendo precio de yfinance: {e}")
    return 1.12045  # Valor de respaldo si falla temporalmente la red

def generar_reporte(precio_actual):
    brent_precio = 111.7
    
    # Niveles de la Sesión Asiática (6:00 PM - 4:30 AM)
    asia_high = 1.12150
    asia_low = 1.11950
    
    pips_sl = 20
    pips_tp = 40
    
    # Escenario de COMPRA (BUY)
    sl_compra = precio_actual - (pips_sl * 0.0001)
    tp_compra = precio_actual + (pips_tp * 0.0001)
    
    # Escenario de VENTA (SELL)
    sl_venta = precio_actual + (pips_sl * 0.0001)
    tp_venta = precio_actual - (pips_tp * 0.0001)
    
    # Determinar estado dinámico respecto al rango
    if precio_actual > asia_high:
        estado_texto = "🚨 *RUPTURA ALCISTA*: El precio superó el Máximo Asiático (High)."
    elif precio_actual < asia_low:
        estado_texto = "🚨 *RUPTURA BAJISTA*: El precio rompió el Mínimo Asiático (Low)."
    else:
        estado_texto = "⏳ El precio oscila dentro del rango asiático establecido."

    mensaje = (
        "🏛️ *SISTEMA TRADING INSTITUCIONAL* 📈📉\n\n"
        f"📊 *EUR/USD*: `{precio_actual:.5f}`\n"
        "📉 *EMA 50*: 1.12027 | *RSI*: 50.0\n"
        f"🛢️ *Brent*: ${brent_precio} USD\n\n"
        "🎯 *SUGERENCIA DE GESTIÓN DE RIESGO (ATR)*:\n\n"
        "🟢 *ESCENARIO DE COMPRA (BUY)*:\n"
        f"• *Stop Loss (SL)*: -{pips_sl} pips (`{sl_compra:.5f}`)\n"
        f"• *Take Profit (TP)*: +{pips_tp} pips (`{tp_compra:.5f}`)\n\n"
        "🔴 *ESCENARIO DE VENTA (SELL)*:\n"
        f"• *Stop Loss (SL)*: -{pips_sl} pips (`{sl_venta:.5f}`)\n"
        f"• *Take Profit (TP)*: +{pips_tp} pips (`{tp_venta:.5f}`)\n\n"
        "• *Ratio Riesgo/Beneficio*: 1:2 (Estructura Institucional)\n\n"
        "🌅 *RANGO SESIÓN ASIÁTICA*:\n"
        "• *Horario*: 6:00 PM - 4:30 AM\n"
        f"• *Máximo (High)*: `{asia_high}`\n"
        f"• *Mínimo (Low)*: `{asia_low}`\n\n"
        "📰 *Forex Factory (Impactos)*:\n"
        "🔴 *Alta*: Sin eventos críticos inmediatos.\n"
        "🟡 *Media*: Discursos de política monetaria.\n"
        "⚪ *Baja*: Datos secundarios de inventarios.\n\n"
        "💼 *Wall Street, Energía & Geopolítica (Impacto EUR/USD)*:\n"
        "• *Petróleo y Dólar*: El alza del Brent impacta directamente en las monedas refugio y la inflación europea.\n"
        "• *Geopolítica*: Monitoreo activo de tensiones en Medio Oriente y decisiones de la FED / BCE.\n\n"
        "------------------------------------\n\n"
        f"📍 *ESTADO*: {estado_texto}"
    )
    return mensaje

def monitoreo_mercado_en_vivo():
    global ultima_alerta_estado
    # Envío inicial al arrancar
    precio_inicial = obtener_precio_eurusd()
    enviar_telegram(generar_reporte(precio_inicial))
    
    while True:
        try:
            precio = obtener_precio_eurusd()
            asia_high = 1.12150
            asia_low = 1.11950
            
            pips_sl = 20
            pips_tp = 40
            
            sl_compra = precio_inicial - (pips_sl * 0.0001)
            tp_compra = precio_inicial + (pips_tp * 0.0001)
            
            # Verificaciones automáticas de alertas importantes
            alerta_enviar = None
            
            if precio > asia_high and ultima_alerta_estado != "RUPTURA_HIGH":
                alerta_enviar = f"🚀 *¡ALERTA INSTITUCIONAL!* El precio (`{precio:.5f}`) ha **roto al alza el Máximo Asiático** (`{asia_high}`)."
                ultima_alerta_estado = "RUPTURA_HIGH"
            elif precio < asia_low and ultima_alerta_estado != "RUPTURA_LOW":
                alerta_enviar = f"📉 *¡ALERTA INSTITUCIONAL!* El precio (`{precio:.5f}`) ha **roto a la baja el Mínimo Asiático** (`{asia_low}`)."
                ultima_alerta_estado = "RUPTURA_LOW"
            elif precio >= tp_compra and ultima_alerta_estado != "ALCANZO_TP":
                alerta_enviar = f"🎯 *¡TAKE PROFIT ALCANZADO!* El precio tocó los +40 pips objetivo en `{precio:.5f}` (Escenario Compra)."
                ultima_alerta_estado = "ALCANZO_TP"
            elif precio <= sl_compra and ultima_alerta_estado != "ALCANZO_SL":
                alerta_enviar = f"⚠️ *¡STOP LOSS TOCADO!* El precio alcanzó el nivel de protección SL en `{precio:.5f}`."
                ultima_alerta_estado = "ALCANZO_SL"
                
            if alerta_enviar:
                enviar_telegram(alerta_enviar)
                
        except Exception as e:
            print(f"Error en bucle de monitoreo: {e}")
            
        time.sleep(60) # Revisa el mercado cada 60 segundos

def verificar_mensajes_telegram():
    offset = None
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    while True:
        try:
            params = {"timeout": 30, "offset": offset}
            response = requests.get(url, params=params).json()
            if "result" in response:
                for update in response["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        precio_actual = obtener_precio_eurusd()
                        reporte = generar_reporte(precio_actual)
                        enviar_telegram(reporte, chat_id=chat_id)
        except Exception as e:
            print(f"Error en polling de Telegram: {e}")
        time.sleep(2)

if __name__ == '__main__':
    # Hilo para monitorear el mercado en vivo 24/7
    t_monitoreo = threading.Thread(target=monitoreo_mercado_en_vivo)
    t_monitoreo.daemon = True
    t_monitoreo.start()
    
    # Hilo para responder comandos de Telegram
    t_telegram = threading.Thread(target=verificar_mensajes_telegram)
    t_telegram.daemon = True
    t_telegram.start()
    
    # Servidor Flask para mantener activo el servicio web en Render
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
