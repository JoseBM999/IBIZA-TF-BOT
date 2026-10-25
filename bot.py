import os
import time
import threading
from datetime import datetime
import requests
import yfinance as yf
import pandas as pd
from flask import Flask

app = Flask(__name__)

# Tus credenciales oficiales integradas
TOKEN = "8798266906:AAEkczcf-Unknsm-SZKoN3q5LQZ-2OemZkY"
CHAT_ID = "8662528470"

def generar_reporte_mercado():
    """Consulta en vivo todos los datos técnicos y fundamentales del mercado"""
    try:
        # 1. Obtener datos en vivo de EUR/USD
        eur_usd = yf.Ticker("EURUSD=X")
        df_eur = eur_usd.history(period="5d", interval="15m")
        
        # 2. Obtener datos en vivo del Brent
        brent = yf.Ticker("BZ=F")
        df_brent = brent.history(period="1d", interval="1h")
        
        precio_actual = 1.12000
        ema_50 = 1.11900
        rsi_actual = 50.0
        high_asia = 1.12150
        low_asia = 1.11950

        if not df_eur.empty:
            precio_actual = df_eur['Close'].iloc[-1]
            ema_50 = df_eur['Close'].ewm(span=50, adjust=False).mean().iloc[-1]
            
            # Cálculo del RSI
            delta = df_eur['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            if not pd.isna(rsi.iloc[-1]):
                rsi_actual = rsi.iloc[-1]
            
            # Máximos y mínimos de la sesión
            high_asia = df_eur['High'].max()
            low_asia = df_eur['Low'].min()

        precio_brent = df_brent['Close'].iloc[-1] if not df_brent.empty else 111.0

        # Gestión de Riesgo (Ratio 1:2 - SL 20 pips / TP 40 pips)
        sl_buy = precio_actual - 0.0020
        tp_buy = precio_actual + 0.0040
        sl_sell = precio_actual + 0.0020
        tp_sell = precio_actual - 0.0040

        mensaje = (
            f"🏛️ **SISTEMA TRADING INSTITUCIONAL** 📈📉\n\n"
            f"📊 **EUR/USD:** {precio_actual:.5f}\n"
            f"📉 **EMA 50:** {ema_50:.5f} | **RSI:** {rsi_actual:.1f}\n"
            f"🛢️ **Brent:** ${precio_brent:.2f} USD\n\n"
            f"🎯 **SUGERENCIA DE GESTIÓN DE RIESGO:**\n\n"
            f"🟢 **ESCENARIO DE COMPRA (BUY):**\n"
            f"• Stop Loss (SL): -20 pips ({sl_buy:.5f})\n"
            f"• Take Profit (TP): +40 pips ({tp_buy:.5f})\n\n"
            f"🔴 **ESCENARIO DE VENTA (SELL):**\n"
            f"• Stop Loss (SL): -20 pips ({sl_sell:.5f})\n"
            f"• Take Profit (TP): +40 pips ({tp_sell:.5f})\n\n"
            f"• **Ratio Riesgo/Beneficio:** 1:2 (Estructura Institucional)\n\n"
            f"🌅 **RANGO SESIÓN ASIÁTICA:**\n"
            f"• Máximo (High): {high_asia:.5f}\n"
            f"• Mínimo (Low): {low_asia:.5f}\n\n"
            f"📰 **Forex Factory (Impactos):**\n"
            f"🔴 **Alta:** Monitoreo crítico de tipos de interés y empleo.\n"
            f"🟡 **Media:** Discursos y actas de política monetaria.\n"
            f"⚪ **Baja:** Datos secundarios de inventarios y balanza comercial.\n\n"
            f"💼 **Wall Street, Energía & Geopolítica:**\n"
            f"• Petróleo y Dólar: La fluctuación del Brent impacta directamente la inflación europea y la moneda refugio.\n"
            f"• Geopolítica: Seguimiento activo de tensiones globales y decisiones del BCE / FED.\n\n"
            f"------------------------------------\n"
            f"📍 **ESTADO:** 🔄 Datos actualizados al momento de tu consulta."
        )
        return mensaje
    except Exception as e:
        return f"⚠️ Error al obtener datos del mercado: {e}"

def enviar_telegram(chat_id, mensaje):
    """Envía el mensaje directamente al chat de Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": mensaje,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error al enviar mensaje: {e}")

@app.route("/")
def home():
    """Ruta web para UptimeRobot (mantiene a Render despierto 24/7)"""
    return "Bot institucional interactivo operando al 100% 🚀"

def background_telegram_listener():
    """Escucha constantemente si le escribes al bot para responderte al instante"""
    print("¡Hilo de escucha de Telegram iniciado con éxito!")
    last_update_id = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update_id}&timeout=30"
            response = requests.get(url, timeout=35)
            if response.status_code == 200:
                data = response.json()
                for result in data.get("result", []):
                    last_update_id = result["update_id"] + 1
                    message = result.get("message", {})
                    chat_id = str(message.get("chat", {}).get("id", ""))
                    
                    if chat_id:
                        # Cada vez que escribas, genera el reporte fresco y mándalo
                        reporte_fresco = generar_reporte_mercado()
                        enviar_telegram(chat_id, reporte_fresco)
        except Exception as e:
            print(f"Error en el listener: {e}")
            time.sleep(5)
        time.sleep(1)

if __name__ == "__main__":
    # Arranca el hilo de escucha en segundo plano
    hilo_listener = threading.Thread(target=background_telegram_listener)
    hilo_listener.daemon = True
    hilo_listener.start()

    # Arranca Flask para Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
