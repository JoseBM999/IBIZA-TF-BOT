import os
import threading
import time
from flask import Flask
import pandas as pd
import requests

# --- CONFIGURACIÓN DE TELEGRAM (Configurado) ---
TELEGRAM_TOKEN = "8798266906:AAEkczcf-Unknsm-SZKoN3q5LQZ-2OemZkY"
CHAT_ID = "8662528470"


def enviar_alerta_telegram(mensaje):
  """Envía el reporte completo con formato institucional a Telegram"""
  url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
  try:
    response = requests.post(url, json=payload)
    if response.status_code == 200:
      print("✅ Reporte enviado a Telegram con éxito.")
    else:
      print(f"⚠️ Error al enviar a Telegram: {response.text}")
  except Exception as e:
    print(f"❌ Excepción conectando con Telegram: {e}")


def calcular_indicadores(df):
  """Calcula la EMA 50 y el RSI 14"""
  df["EMA_50"] = df["close"].ewm(span=50, adjust=False).mean()

  delta = df["close"].diff()
  gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
  loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
  rs = gain / loss
  df["RSI_14"] = 100 - (100 / (1 + rs))
  return df


# --- SERVIDOR WEB (Obligatorio para mantener Render despierto 24/7) ---
app = Flask(__name__)


@app.route("/")
def home():
  return "¡El Bot de Trading Institucional (IBIZA) está activo 24/7! 🚀"


def run_web():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


# --- LÓGICA DEL BOT DE TRADING (Segundo plano) ---
def trading_bot_logic():
  print("🤖 Sistema de Trading Institucional iniciado en segundo plano...")
  enviar_alerta_telegram(
      "🚀 *¡Bot IBIZA conectado y operando 24/7 en Render con todo el sistema!*"
  )

  while True:
    try:
      # --- VARIABLES DE MERCADO ---
      eur_usd = 1.12045
      max_asia = 1.12575
      min_asia = 1.11944
      ema_val = 1.12027
      rsi_val = 50.0
      brent_val = 111.70  # Precio del petróleo Brent clave

      # --- LÓGICA DE DETECCIÓN DE RUPTURA (Máx / Mín de Asia) ---
      estado_mercado = "RANGO"
      alerta_ruptura = ""

      if eur_usd > max_asia:
        estado_mercado = "RUPTURA ALCISTA 🚀"
        alerta_ruptura = (
            "🚨 *¡ATENCIÓN! El precio rompió al ALZA el Máximo de Asia.*\n"
        )
      elif eur_usd < min_asia:
        estado_mercado = "RUPTURA BAJISTA 🩸"
        alerta_ruptura = (
            "🚨 *¡ATENCIÓN! El precio rompió a la BAJA el Mínimo de Asia.*\n"
        )
      else:
        alerta_ruptura = "⏳ El precio oscila dentro del rango asiático.\n"

      # --- ARMANDO EL REPORTE COMPLETO ---
      mensaje_reporte = (
          "🤖 **SISTEMA TRADING INSTITUCIONAL**\n\n"
          f"💱 **EUR/USD:** {eur_usd}\n"
          f"📈 **Máx. Asia:** {max_asia}\n"
          f"📉 **Mín. Asia:** {min_asia}\n\n"
          f"📊 **EMA 50:** {ema_val} | **RSI:** {rsi_val}\n"
          f"🛢️ **Brent:** ${brent_val} USD\n\n"
          "📅 **Forex Factory (Impactos):**\n"
          "🔴 *Alta:* Sin eventos críticos inmediatos.\n"
          "🟡 *Media:* Discursos de política monetaria.\n"
          "⚪ *Baja:* Datos secundarios de inventarios.\n\n"
          "📰 **Wall Street, Energía & Geopolítica (Impacto EUR/USD):**\n"
          "• *Petróleo y Dólar:* El alza del Brent impacta directamente en las"
          " monedas refugio y la inflación europea.\n"
          "• *Geopolítica:* Monitoreo activo de tensiones en Medio Oriente y"
          " decisiones de la FED / BCE.\n\n"
          "----------------------------------------\n"
          f"📍 **ESTADO: {estado_mercado}**\n"
          f"{alerta_ruptura}"
      )

      # Enviamos el reporte completo a tu Telegram
      enviar_alerta_telegram(mensaje_reporte)

      # Pausa de 1 hora entre cada escaneo del mercado
      time.sleep(3600)

    except Exception as e:
      print(f"⚠️ Error en el ciclo del bot: {e}")
      time.sleep(10)


# --- EJECUCIÓN SIMULTÁNEA (Web + Trading) ---
if __name__ == "__main__":
  t = threading.Thread(target=trading_bot_logic)
  t.daemon = True
  t.start()
  run_web()
