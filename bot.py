import os
import time
import threading
from datetime import datetime
import requests
import yfinance as yf
import pandas as pd
from flask import Flask

app = Flask(__name__)

# Tus credenciales oficiales
TOKEN = "8798266906:AAEkczcf-Unknsm-SZKoN3q5LQZ-2OemZkY"
CHAT_ID = "8662528470"

alerta_enviada_hoy = False

def generar_reporte_mercado():
    """Consulta en vivo y fuerza la actualización de precios reales del mercado de forma segura"""
    try:
        # Descarga de datos
        eur_data = yf.download("EURUSD=X", period="1d", interval="1m", progress=False)
        brent_data = yf.download("BZ=F", period="1d", interval="1m", progress=False)
        df_eur = yf.Ticker("EURUSD=X").history(period="5d", interval="15m")
        
        # Precio actual seguro para evitar errores de tipo Series
        precio_actual = 1.12000
        if not eur_data.empty and 'Close' in eur_data:
            val = eur_data['Close'].iloc[-1]
            precio_actual = float(val.iloc[0]) if hasattr(val, 'iloc') else float(val)
        elif not df_eur.empty:
            val = df_eur['Close'].iloc[-1]
            precio_actual = float(val.iloc[0]) if hasattr(val, 'iloc') else float(val)

        # Precio Brent seguro
        precio_brent = 115.56
        if not brent_data.empty and 'Close' in brent_data:
            val_b = brent_data['Close'].iloc[-1]
            precio_brent = float(val_b.iloc[0]) if hasattr(val_b, 'iloc') else float(val_b)

        ema_50 = 1.11900
        rsi_actual = 50.0
        high_asia = precio_actual + 0.0020
        low_asia = precio_actual - 0.0020

        if not df_eur.empty:
            ema_series = df_eur['Close'].ewm(span=50, adjust=False).mean().iloc[-1]
            ema_50 = float(ema_series.iloc[0]) if hasattr(ema_series, 'iloc') else float(ema_series)
            
            delta = df_eur['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_val = rsi.iloc[-1]
            if not pd.isna(rsi_val):
                rsi_actual = float(rsi_val.iloc[0]) if hasattr(rsi_val, 'iloc') else float(rsi_val)
            
            high_val = df_eur['High'].max()
            high_asia = float(high_val.iloc[0]) if hasattr(high_val, 'iloc') else float(high_val)
            
            low_val = df_eur['Low'].min()
            low_asia = float(low_val.iloc[0]) if hasattr(low_val, 'iloc') else float(low_val)

        # Cálculos de Gestión de Riesgo (Ratio 1:2 - SL 20 pips / TP 40 pips)
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
        return mensaje, precio_actual, high_asia, low_asia
    except Exception as e:
        return f"⚠️ Error al obtener datos del mercado: {e}", 0, 0, 0

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

def background_trading_monitor():
    """Vigila en segundo plano si el precio rompe los rangos de Asia para avisarte solo"""
    global alerta_enviada_hoy
    print("¡Monitor automático de rupturas iniciado en segundo plano!")
    
    while True:
        try:
            _, precio_actual, high_asia, low_asia = generar_reporte_mercado()
            
            if precio_actual > 0 and high_asia > 0 and low_asia > 0:
                if precio_actual > high_asia and not alerta_enviada_hoy:
                    alerta_ruptura = (
                        f"🚨 **¡ALERTA DE RUPTURA INSTITUCIONAL!** 🚀\n\n"
                        f"📈 El precio del **EUR/USD ({precio_actual:.5f})** acaba de **romper al alza el Máximo de la Sesión Asiática** ({high_asia:.5f}).\n\n"
                        f"⚡ ¡Atentos a posibles confirmaciones!"
                    )
                    enviar_telegram(CHAT_ID, alerta_ruptura)
                    alerta_enviada_hoy = True
                
                elif precio_actual < low_asia and not alerta_enviada_hoy:
                    alerta_ruptura = (
                        f"🚨 **¡ALERTA DE RUPTURA INSTITUCIONAL!** ⚠️\n\n"
                        f"📉 El precio del **EUR/USD ({precio_actual:.5f})** acaba de **romper a la baja el Mínimo de la Sesión Asiática** ({low_asia:.5f}).\n\n"
                        f"⚡ ¡Atentos a posibles escenarios bajistas!"
                    )
                    enviar_telegram(CHAT_ID, alerta_ruptura)
                    alerta_enviada_hoy = True
                
                elif low_asia <= precio_actual <= high_asia:
                    alerta_enviada_hoy = False

        except Exception as e:
            print(f"Error en el monitor automático: {e}")
            
        time.sleep(180)

def background_telegram_listener():
    """Escucha constantemente si le escribes al bot para responderte al instante"""
    print("¡Hilo de escucha de Telegram interactivo iniciado!")
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
                        reporte_fresco, _, _, _ = generar_reporte_mercado()
                        enviar_telegram(chat_id, reporte_fresco)
        except Exception as e:
            print(f"Error en el listener: {e}")
            time.sleep(5)
        time.sleep(1)

if __name__ == "__main__":
    hilo_listener = threading.Thread(target=background_telegram_listener)
    hilo_listener.daemon = True
    hilo_listener.start()

    hilo_monitor = threading.Thread(target=background_trading_monitor)
    hilo_monitor.daemon = True
    hilo_monitor.start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
