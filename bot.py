import os
import time
import threading
from datetime import datetime
import requests
import yfinance as yf
from flask import Flask

app = Flask(__name__)

# Configuración de Telegram (Usa tu nuevo token limpio de BotFather)
TOKEN = os.environ.get("TELEGRAM_TOKEN", "TU_TOKEN_NUEVO_DE_BOTFATHER")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "TU_CHAT_ID")

def enviar_telegram(mensaje):
    """Función para enviar mensajes directos a tu Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": mensaje,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error al enviar mensaje a Telegram: {e}")

@app.route("/")
def home():
    """Ruta web para que UptimeRobot mantenga vivo a Render 24/7"""
    return "Bot institucional de EUR/USD en tiempo real operando 🚀"

def calcular_rsi(series, period=14):
    """Calcula el RSI técnico en base a los precios"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def background_trading_loop():
    """Ciclo en segundo plano que analiza el mercado en vivo"""
    print("¡Hilo de trading institucional en tiempo real iniciado!")
    
    while True:
        try:
            # 1. Obtener datos en vivo de EUR/USD
            eur_usd = yf.Ticker("EURUSD=X")
            df_eur = eur_usd.history(period="5d", interval="15m")
            
            # 2. Obtener datos en vivo del Brent
            brent = yf.Ticker("BZ=F")
            df_brent = brent.history(period="1d", interval="1h")
            
            if not df_eur.empty:
                precio_actual = df_eur['Close'].iloc[-1]
                
                # Calcular EMA 50
                ema_50 = df_eur['Close'].ewm(span=50, adjust=False).mean().iloc[-1]
                
                # Calcular RSI
                rsi_actual = calcular_rsi(df_eur['Close'])
                if pd.isna(rsi_actual):
                    rsi_actual = 50.0

            if not df_brent.empty:
                precio_brent = df_brent['Close'].iloc[-1]
            else:
                precio_brent = 111.0 # Valor por defecto de respaldo

            # Simulación de máximos y mínimos de la sesión asiática en base a las últimas velas
            high_asia = df_eur['High'].max() if not df_eur.empty else precio_actual + 0.0020
            low_asia = df_eur['Low'].min() if not df_eur.empty else precio_actual - 0.0020

            # Cálculos de Gestión de Riesgo (Estructura 1:2 - SL 20 pips / TP 40 pips aprox)
            sl_buy = precio_actual - 0.0020
            tp_buy = precio_actual + 0.0040
            
            sl_sell = precio_actual + 0.0020
            tp_sell = precio_actual - 0.0040

            # Construir el reporte institucional actualizado
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
                f"------------------------------------\n"
                f"📍 **ESTADO:** ⏳ Monitoreando variaciones del mercado en vivo."
            )

            # Aquí puedes mandar la alerta automática o programar tus intervalos de envío
            # enviar_telegram(mensaje)

        except Exception as e:
            print(f"Error al actualizar datos de mercado: {e}")
        
        # Espera 5 minutos antes de volver a consultar el mercado en tiempo real
        time.sleep(300)

if __name__ == "__main__":
    # Iniciar el bot de trading en segundo plano
    hilo_bot = threading.Thread(target=background_trading_loop)
    hilo_bot.daemon = True
    hilo_bot.start()

    # Iniciar Flask para Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
