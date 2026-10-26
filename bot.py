import os
import time
import threading
from datetime import datetime, timezone, timedelta
import requests
import yfinance as yf
import pandas as pd
from flask import Flask

app = Flask(__name__)

# Tus credenciales oficiales
TOKEN = "8798266906:AAEkczcf-Unknsm-SZKoN3q5LQZ-2OemZkY"
CHAT_ID = "8662528470"

alerta_enviada_hoy = False

def obtener_noticias_forex_factory():
    """Consume el feed oficial en vivo del calendario de Forex Factory"""
    try:
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            events = response.json()
            colombia_tz = timezone(timedelta(hours=-5))
            hoy_str = datetime.now(colombia_tz).strftime('%Y-%m-%d')
            noticias_hoy = [e for e in events if e.get('date', '').startswith(hoy_str)]
            
            if not noticias_hoy:
                noticias_hoy = events[:5]
            
            texto_gris = ""
            for event in noticias_hoy[:6]:
                title = event.get('title', '')
                country = event.get('country', '')
                date_raw = event.get('date', '')
                time_str = date_raw[11:16] if len(date_raw) >= 16 else ""
                texto_gris += f"• [{country}] {title} ({time_str})\n"
                
            if texto_gris:
                return f"⚪ **Carpeta Blanca/Gris (Baja/Actualizados):**\n{texto_gris}"
    except Exception as e:
        print(f"Error noticias: {e}")
    return "• Monitoreo activo: Sin eventos críticos en este bloque."

def generar_reporte_mercado():
    """Genera el reporte extrayendo precio, EMA, RSI y rangos 100% de la misma fuente (yfinance) para evitar desajustes"""
    try:
        # Descarga de datos de yfinance para EUR/USD y Brent
        eur = yf.download("EURUSD=X", period="2d", interval="15m", progress=False)
        brent = yf.download("BZ=F", period="2d", interval="1h", progress=False)

        if isinstance(eur.columns, pd.MultiIndex):
            eur.columns = eur.columns.get_level_values(0)
        if isinstance(brent.columns, pd.MultiIndex):
            brent.columns = brent.columns.get_level_values(0)

        if eur.empty or 'Close' not in eur.columns:
            raise ValueError("No se pudieron descargar los datos de EUR/USD.")
        if brent.empty or 'Close' not in brent.columns:
            raise ValueError("No se pudieron descargar los datos del Brent.")

        close_series = eur['Close'].dropna()
        if len(close_series) == 0:
            raise ValueError("La serie de cierre de EUR/USD está vacía.")

        # Precio actual exactamente igual al último cierre de la vela de yfinance (sincronizado con TradingView)
        precio_actual = float(close_series.iloc[-1].item() if hasattr(close_series.iloc[-1], 'item') else close_series.iloc[-1])

        # Cálculo de EMA 50 usando la misma serie de velas
        ema_series = close_series.ewm(span=50, adjust=False).mean()
        ema_50 = float(ema_series.iloc[-1].item() if hasattr(ema_series.iloc[-1], 'item') else ema_series.iloc[-1])

        # Cálculo de RSI 14 usando la misma serie de velas (sin interferencias externas)
        delta = close_series.diff()
        gain = delta.clip(lower=0).rolling(window=14).mean()
        loss = (-delta.clip(upper=0)).rolling(window=14).mean()
        
        g_val = gain.iloc[-1]
        l_val = loss.iloc[-1]
        g_val = float(g_val.item() if hasattr(g_val, 'item') else g_val) if not pd.isna(g_val) else 0.0
        l_val = float(l_val.item() if hasattr(l_val, 'item') else l_val) if not pd.isna(l_val) else 0.0

        if l_val > 0:
            rs = g_val / l_val
            rsi_calc = 100 - (100 / (1 + rs))
            rsi_actual = float(rsi_calc.item() if hasattr(rsi_calc, 'item') else rsi_calc)
        else:
            rsi_actual = 50.0

        # Rangos de la Sesión Asiática y Brent
        high_asia = float(eur['High'].max().item() if hasattr(eur['High'].max(), 'item') else eur['High'].max())
        low_asia = float(eur['Low'].min().item() if hasattr(eur['Low'].min(), 'item') else eur['Low'].min())

        brent_series = brent['Close'].dropna()
        precio_brent = float(brent_series.iloc[-1].item() if hasattr(brent_series.iloc[-1], 'item') else brent_series.iloc[-1])

        # Gestión de riesgo institucional 1:2
        sl_buy = precio_actual - 0.0020
        tp_buy = precio_actual + 0.0040
        sl_sell = precio_actual + 0.0020
        tp_sell = precio_actual - 0.0040

        noticias_rf = obtener_noticias_forex_factory()

        # Hora exacta en Colombia (UTC-5)
        colombia_tz = timezone(timedelta(hours=-5))
        hora_exacta = datetime.now(colombia_tz).strftime('%Y-%m-%d %H:%M:%S')

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
            f"• Take Profit (TP): -40 pips ({tp_sell:.5f})\n\n"
            f"• **Ratio Riesgo/Beneficio:** 1:2 (Estructura Institucional)\n\n"
            f"🌅 **RANGO SESIÓN ASIÁTICA:**\n"
            f"• Máximo (High): {high_asia:.5f}\n"
            f"• Mínimo (Low): {low_asia:.5f}\n\n"
            f"📰 **Forex Factory (Noticias en Vivo):**\n"
            f"{noticias_rf}\n\n"
            f"💼 **Wall Street, Energía & Geopolítica:**\n"
            f"• Petróleo y Dólar: La fluctuación del Brent impacta directamente la inflación europea y la moneda refugio.\n"
            f"• Geopolítica: Seguimiento activo de tensiones globales y decisiones del BCE / FED.\n\n"
            f"------------------------------------\n"
            f"📍 **ESTADO:** 🔄 Sincronizado 100% con velas en vivo\n"
            f"⏱️ **Hora Colombia:** {hora_exacta}"
        )
        return mensaje, precio_actual, high_asia, low_asia
    except Exception as e:
        error_msg = f"⚠️ **Error en el motor de datos:** {str(e)}\n*Por favor verifica la conexión con los servidores en la nube.*"
        return error_msg, 0, 0, 0

def enviar_telegram(chat_id, mensaje):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": mensaje, "parse_mode": "Markdown"}
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error al enviar: {e}")

@app.route("/")
def home():
    return "Bot institucional sincronizado operando al 100% 🚀"

def background_trading_monitor():
    global alerta_enviada_hoy
    while True:
        try:
            _, precio_actual, high_asia, low_asia = generar_reporte_mercado()
            if precio_actual > 0 and high_asia > 0 and low_asia > 0:
                if precio_actual > high_asia and not alerta_enviada_hoy:
                    enviar_telegram(CHAT_ID, f"🚨 **¡ALERTA DE RUPTURA AL ALZA!** 🚀\nEUR/USD ({precio_actual:.5f}) rompió el Máximo de Asia ({high_asia:.5f}).")
                    alerta_enviada_hoy = True
                elif precio_actual < low_asia and not alerta_enviada_hoy:
                    enviar_telegram(CHAT_ID, f"🚨 **¡ALERTA DE RUPTURA A LA BAJA!** ⚠️\nEUR/USD ({precio_actual:.5f}) rompió el Mínimo de Asia ({low_asia:.5f}).")
                    alerta_enviada_hoy = True
                elif low_asia <= precio_actual <= high_asia:
                    alerta_enviada_hoy = False
        except Exception as e:
            print(f"Error en monitor: {e}")
        time.sleep(180)

def background_telegram_listener():
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
            print(f"Error listener: {e}")
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
