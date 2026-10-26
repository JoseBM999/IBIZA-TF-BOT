import os
import time
import threading
from datetime import datetime, timezone, timedelta
import requests
import yfinance as yf
import pandas as pd
import xml.etree.ElementTree as ET
from flask import Flask

app = Flask(__name__)

# Tus credenciales oficiales
TOKEN = "8798266906:AAEkczcf-Unknsm-SZKoN3q5LQZ-2OemZkY"
CHAT_ID = "8662528470"

alerta_enviada_hoy = False

def obtener_noticias_forex_factory():
    """Consume el feed oficial en vivo. Si no hay datos o falla, retorna vacío (cero texto estático)."""
    try:
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            events = response.json()
            colombia_tz = timezone(timedelta(hours=-5))
            hoy_str = datetime.now(colombia_tz).strftime('%Y-%m-%d')
            noticias_hoy = [e for e in events if e.get('date', '').startswith(hoy_str)]
            
            texto_gris = ""
            for event in noticias_hoy[:6]:
                title = event.get('title', '')
                country = event.get('country', '')
                date_raw = event.get('date', '')
                time_str = date_raw[11:16] if len(date_raw) >= 16 else ""
                texto_gris += f"• [{country}] {title} ({time_str})\n"
                
            if texto_gris:
                return f"📰 **Forex Factory (En Vivo):**\n{texto_gris}"
    except Exception as e:
        print(f"Error noticias FF: {e}")
    return ""

def obtener_noticias_wall_street():
    """Consume los titulares de CNBC en vivo. Si falla, retorna vacío (cero texto estático)."""
    try:
        url = "https://www.cnbc.com/id/10000664/device/rss/rss.html"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            items = root.findall('.//item')[:3]
            texto = ""
            for item in items:
                title = item.find('title')
                if title is not None and title.text:
                    texto += f"• {title.text}\n"
            if texto:
                return f"💼 **Wall Street & Mercados (En Vivo):**\n{texto}"
    except Exception as e:
        print(f"Error WS news: {e}")
    return ""

def generar_reporte_mercado():
    """Genera el reporte extrayendo 100% datos de la nube sin bloques de texto fijo"""
    try:
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

        # Precio actual sincronizado con el último cierre de la vela
        precio_actual = float(close_series.iloc[-1].item() if hasattr(close_series.iloc[-1], 'item') else close_series.iloc[-1])

        # Cálculo de EMA 50
        ema_series = close_series.ewm(span=50, adjust=False).mean()
        ema_50 = float(ema_series.iloc[-1].item() if hasattr(ema_series.iloc[-1], 'item') else ema_series.iloc[-1])

        # Cálculo de RSI 14 (Estándar Wilder / TradingView)
        delta = close_series.diff()
        gain = delta.clip(lower=0)
        loss = (-delta.clip(upper=0))
        
        avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
        
        rs = avg_gain / avg_loss
        rsi_series = 100 - (100 / (1 + rs))
        rsi_actual = float(rsi_series.iloc[-1].item() if hasattr(rsi_series.iloc[-1], 'item') else rsi_series.iloc[-1])

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
        noticias_ws = obtener_noticias_wall_street()

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
            f"• Mínimo (Low): {low_asia:.5f}\n"
        )

        # Se añaden las secciones de noticias únicamente si hay datos frescos de la nube
        if noticias_rf:
            mensaje += f"\n{noticias_rf}"
        if noticias_ws:
            mensaje += f"\n{noticias_ws}"

        mensaje += (
            f"\n------------------------------------\n"
            f"📍 **ESTADO:** 🔄 100% Cloud Data (Cero textos estáticos)\n"
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
    return "Bot institucional dinámico sin textos fijos operando al 100% 🚀"

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
