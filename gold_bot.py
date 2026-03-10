import requests
import pandas as pd
import numpy as np
import time
from config import *

print("🚀 GOLD AI BOT STARTED")

# =========================
# TELEGRAM
# =========================

def send_telegram(msg):

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }

    requests.post(url, json=payload)


# =========================
# GET DATA
# =========================

def get_data(interval):

    url = "https://api.twelvedata.com/time_series"

    params = {
        "symbol": SYMBOL,
        "interval": interval,
        "outputsize": 200,
        "apikey": API_KEY
    }

    r = requests.get(url, params=params)

    data = r.json()

    if "values" not in data:
        print("API ERROR:", data)
        return None

    df = pd.DataFrame(data["values"])

    df = df.astype(float)

    df = df[::-1]

    return df


# =========================
# INDICATORS
# =========================

def indicators(df):

    df["ema20"] = df["close"].ewm(span=20).mean()

    df["ema50"] = df["close"].ewm(span=50).mean()

    delta = df["close"].diff()

    gain = delta.clip(lower=0)

    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()

    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss

    df["rsi"] = 100 - (100/(1+rs))

    return df


# =========================
# TREND
# =========================

def trend(df):

    last = df.iloc[-1]

    if last["ema20"] > last["ema50"]:
        return "bullish"

    if last["ema20"] < last["ema50"]:
        return "bearish"

    return "neutral"


# =========================
# BREAKOUT DETECTION
# =========================

def breakout(df):

    high = df["high"].rolling(20).max().iloc[-1]

    low = df["low"].rolling(20).min().iloc[-1]

    price = df.iloc[-1]["close"]

    if price > high:
        return "break_up"

    if price < low:
        return "break_down"

    return None


# =========================
# ANALYZE
# =========================

def analyze(df_m1, df_m5, df_m15):

    trend_m5 = trend(df_m5)

    trend_m15 = trend(df_m15)

    last = df_m1.iloc[-1]

    price = last["close"]

    rsi = last["rsi"]

    if trend_m5 == "bullish" and trend_m15 == "bullish" and rsi < 65:

        entry = price

        sl = price - 2

        tp = price + 4

        return {
            "type":"BUY",
            "entry":entry,
            "sl":sl,
            "tp":tp
        }

    if trend_m5 == "bearish" and trend_m15 == "bearish" and rsi > 35:

        entry = price

        sl = price + 2

        tp = price - 4

        return {
            "type":"SELL",
            "entry":entry,
            "sl":sl,
            "tp":tp
        }

    return None


# =========================
# MAIN LOOP
# =========================

while True:

    try:

        df_m1 = get_data("1min")

        df_m5 = get_data("5min")

        df_m15 = get_data("15min")

        if df_m1 is None or df_m5 is None or df_m15 is None:

            time.sleep(60)

            continue

        df_m1 = indicators(df_m1)

        df_m5 = indicators(df_m5)

        df_m15 = indicators(df_m15)

        signal = analyze(df_m1, df_m5, df_m15)

        if signal:

            msg = f"""
📊 <b>XAUUSD AI SIGNAL</b>

Type: {signal['type']}

Entry: {round(signal['entry'],2)}

SL: {round(signal['sl'],2)}

TP: {round(signal['tp'],2)}

Timeframe: M1 / M5 / M15
"""

            print(msg)

            send_telegram(msg)

    except Exception as e:

        print("Error:", e)

    time.sleep(CHECK_INTERVAL)
