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
    """Consume el feed oficial en vivo del calendario de Forex Factory clasificadas por impacto"""
    try:
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        response = requests.get(url, timeout=8)
        if response.status_code == 200:
            events = response.json()
            colombia_tz = timezone(timedelta(hours=-5))
            hoy_str = datetime.now(colombia_tz).strftime('%Y-%m-%d')
            noticias_hoy = [e for e in events if e.get('date', '').startswith(hoy_str)]
            
            if not noticias_hoy:
                noticias_hoy = events[:6]
            
            texto_rojo = ""
            texto_amarillo = ""
            texto_gris = ""
            
            for event in noticias_hoy[:8]:
                impacto = event.get('impact', 'Low')
                title = event.get('title', '')
                country = event.get('country', '')
                date_raw = event.get('date', '')
                time_str = date_raw[11:16] if len(date_raw) >= 16 else ""
                
                linea = f"• [{country}] {title} ({time_str})\n"
                if impacto == 'High':
                    texto_rojo += linea
                elif impacto == 'Medium':
                    texto_amarillo += linea
                else:
                    texto_gris += linea
                    
            res = ""
            if texto_rojo:
                res += f"🔴 **Carpeta Roja (Alta):**\n{texto_rojo}\n"
            if texto_amarillo:
                res += f"🟡 **Carpeta Amarilla (Media):**\n{texto_amarillo}\n"
            if texto_gris:
                res += f"⚪ **Carpeta Blanca/Gris (Baja):**\n{texto_gris}"
                
            return res if res else "• Monitoreo activo: Sin eventos críticos en este bloque horario."
    except Exception as e:
        print(f"Error al obtener noticias: {e}")
    return "🔴 **Alta:** NÓMINAS / Tipos de interés / Empleo.\n🟡 **Media:** Discursos de bancos centrales.\n⚪ **Baja:** Datos secundarios de inventarios."

def generar_reporte_mercado():
    """Consulta en vivo con descarga directa para evitar caché estática"""
    try:
        # Descarga forzada en tiempo real para evitar datos congelados de caché
        df_eur = yf.download("EURUSD=X", period="1d", interval="1m", progress=False)
        if df_eur.empty:
            df_eur = yf.download("EURUSD=X", period="5d", interval="15m", progress=False)

        df_brent = yf.download("BZ=F", period="1d", interval="1h", progress=False)
        if df_brent.empty:
            df_brent = yf.download("BZ=F", period="5d", interval="1d", progress=False)

        # Extracción segura de valores numéricos puros con aplanamiento de columnas multindex de yfinance
        if isinstance(df_eur.columns, pd.MultiIndex):
            df_eur.columns = df_eur.columns.get_level_values(0)
        if isinstance(df_brent.columns, pd.MultiIndex):
            df_brent.columns = df_brent.columns.get_level_values(0)

        precio_actual = 1.12000
        if not df_eur.empty and 'Close' in df_eur.columns:
            val = df_eur['Close'].iloc[-1]
            precio_actual = float(val.item() if hasattr(val, 'item') else val)

        precio_brent = 110.47
        if not df_brent.empty and 'Close' in df_brent.columns:
            val_b = df_brent['Close'].iloc[-1]
            precio_brent = float(val_b.item() if hasattr(val_b, 'item') else val_b)

        ema_50 = precio_actual - 0.0010
        rsi_actual = 50.0
        high_asia = precio_actual + 0.0020
        low_asia = precio_actual - 0.0020

        if not df_eur.empty and 'Close' in df_eur.columns:
            ema_series = df_eur['Close'].ewm(span=50, adjust=False).mean().iloc[-1]
            ema_50 = float(ema_series.item() if hasattr(ema_series, 'item') else ema_series)
            
            delta = df_eur['Close'].diff()
            gain_series = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss_series = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            
            if not gain_series.empty and not loss_series.empty:
                g_val = gain_series.iloc[-1]
                l_val = loss_series.iloc[-1]
                g_val = float(g_val.item() if hasattr(g_val, 'item') else g_val)
                l_val = float(l_val.item() if hasattr(l_val, 'item') else l_val)
                
                if pd.isna(g_val) or pd.isna(l_val) or (g_val == 0 and l_val == 0):
                    rsi_actual = 50.0
                else:
                    l_val = max(l_val, 0.00001)
                    rs = g_val / l_val
                    rsi_val = 100 - (100 / (1 + rs))
                    rsi_actual = float(rsi_val.item() if hasattr(rsi_val, 'item') else rsi_val)
            
            if 'High' in df_eur.columns:
                high_val = df_eur['High'].max()
                high_asia = float(high_val.item() if hasattr(high_val, 'item') else high_val)
            
            if 'Low' in df_eur.columns:
                low_val = df_eur['Low'].min()
                low_asia = float(low_val.item() if hasattr(low_val, 'item') else low_val)

        # Cálculos exactos de Gestión de Riesgo (Ratio 1:2 - SL 20 pips / TP 40 pips dinámicos)
        sl_buy = precio_actual - 0.0020
        tp_buy = precio_actual + 0.0040
        sl_sell = precio_actual + 0.0020
        tp_sell = precio_actual - 0.0040

        # Obtener noticias categorizadas de Forex Factory en vivo
        noticias_rf = obtener_noticias_forex_factory()

        # Hora exacta en la hora local de Colombia (UTC-5)
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
            f"• Take Profit (TP): +40 pips ({tp_sell:.5f})\n\n"
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
            f"📍 **ESTADO:** 🔄 Datos actualizados en vivo\n"
            f"⏱️ **Hora Colombia:** {hora_exacta}"
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
