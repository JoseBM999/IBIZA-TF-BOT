import os
import time
import requests
from flask import Flask

# Configuración de credenciales institucionales
TOKEN = "8798266906:AAEkczcf-Unknsm-SZKoN3q5LQZ-2OemZkY"
CHAT_ID = "8662528470"

app = Flask(__name__)

@app.route('/')
def home():
    return "IBIZA-TF-BOT Institucional Activo 24/7"

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

def generar_reporte():
    precio_actual = 1.12045
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
    
    mensaje = (
        "🏛️ *SISTEMA TRADING INSTITUCIONAL* 📈📉\n\n"
        "📊 *EUR/USD*: 1.12045\n"
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
        "📍 *ESTADO*: RANGO\n"
        "⏳ El precio oscila dentro del rango asiático establecido."
    )
    return mensaje

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
                        reporte = generar_reporte()
                        enviar_telegram(reporte, chat_id=chat_id)
        except Exception as e:
            print(f"Error en polling de Telegram: {e}")
        time.sleep(2)

def bucle_principal():
    reporte_inicial = generar_reporte()
    enviar_telegram(reporte_inicial)
    verificar_mensajes_telegram()

if __name__ == '__main__':
    import threading
    t = threading.Thread(target=bucle_principal)
    t.daemon = True
    t.start()
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
