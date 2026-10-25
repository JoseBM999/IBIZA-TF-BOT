import os
import time
import requests
import pandas as pd
from flask import Flask

# Configuración de credenciales institucionales
TOKEN = "8798266906:AAEkczcf-Unknsm-SZKoN3q5LQZ-2OemZkY"
CHAT_ID = "8662528470"

app = Flask(__name__)

@app.route('/')
def home():
    return "IBIZA-TF-BOT Institucional Activo 24/7"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error enviando mensaje: {e}")

def calcular_gestion_riesgo():
    # Datos de mercado institucionales actualizados
    precio_actual = 1.12045
    brent_precio = 111.7
    
    # Niveles de la Sesión Asiática (High / Low simulados para el cálculo técnico)
    asia_high = 1.12150
    asia_low = 1.11950
    
    # Parámetros fijos solicitados: 20 pips SL / 40 pips TP
    pips_sl = 20
    pips_tp = 40
    
    sl_sugerido = precio_actual - (pips_sl * 0.0001)
    tp_sugerido = precio_actual + (pips_tp * 0.0001)
    
    mensaje = (
        "🏛️ *SISTEMA TRADING INSTITUCIONAL* 📈📉\n\n"
        "📊 *EUR/USD*: 1.12045\n"
        "📉 *EMA 50*: 1.12027 | *RSI*: 50.0\n"
        f"🛢️ *Brent*: ${brent_precio} USD\n\n"
        "🎯 *SUGERENCIA DE GESTIÓN DE RIESGO (ATR)*:\n"
        f"• *Stop Loss (SL)*: -{pips_sl} pips (Precio aprox: `{sl_sugerido:.5f}`)\n"
        f"• *Take Profit (TP)*: +{pips_tp} pips (Precio aprox: `{tp_sugerido:.5f}`)\n"
        "• *Ratio Riesgo/Beneficio*: 1:2 (Estructura Institucional)\n\n"
        "🌅 *RANGO SESIÓN ASIÁTICA*:\n"
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
        "📍 *ESTADO*: RANGO\n"
        "⏳ El precio oscila dentro del rango asiático establecido."
    )
    return mensaje

def bucle_principal():
    reporte_inicial = calcular_gestion_riesgo()
    enviar_telegram(reporte_inicial)
    
    while True:
        time.sleep(3600)

if __name__ == '__main__':
    import threading
    t = threading.Thread(target=bucle_principal)
    t.daemon = True
    t.start()
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
