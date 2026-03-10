import requests
import pandas as pd
import numpy as np
import time
import json
from config import *

BASE_URL = "https://api.binance.com/api/v3/klines"

# =============================
# TELEGRAM
# =============================

def send_telegram(msg):

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }

    try:
        requests.post(url, json=payload)
    except:
        pass


# =============================
# GET DATA
# =============================

def get_candles():

    url = f"https://api.binance.com/api/v3/klines"

    params = {
        "symbol":"XAUUSDT",
        "interval":"5m",
        "limit":200
    }

    r = requests.get(url,params=params)

    data = r.json()

    df = pd.DataFrame(data)

    df = df[[1,2,3,4,5]]

    df.columns = ["open","high","low","close","volume"]

    df = df.astype(float)

    return df


# =============================
# INDICATORS
# =============================

def calculate_indicators(df):

    df["ema20"] = df["close"].ewm(span=20).mean()
    df["ema50"] = df["close"].ewm(span=50).mean()

    delta = df["close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss

    df["rsi"] = 100 - (100 / (1 + rs))

    return df


# =============================
# ANALYSIS
# =============================

def analyze(df):

    last = df.iloc[-1]

    trend = "neutral"

    if last["ema20"] > last["ema50"]:
        trend = "bullish"

    if last["ema20"] < last["ema50"]:
        trend = "bearish"

    price = last["close"]

    if trend == "bullish" and last["rsi"] < 65:

        entry = price
        sl = price - 8
        tp = price + 16

        return {
            "type":"BUY",
            "entry":entry,
            "sl":sl,
            "tp":tp
        }

    if trend == "bearish" and last["rsi"] > 35:

        entry = price
        sl = price + 8
        tp = price - 16

        return {
            "type":"SELL",
            "entry":entry,
            "sl":sl,
            "tp":tp
        }

    return None


# =============================
# MAIN LOOP
# =============================

def run():

    print("BOT VÀNG ĐÃ CHẠY")

    while True:

        try:

            df = get_candles()

            df = calculate_indicators(df)

            signal = analyze(df)

            if signal:

                msg = f"""
<b>JUSTINCUA XAUUSD SIGNAL</b>

Type: {signal['type']}

Entry: {round(signal['entry'],2)}

SL: {round(signal['sl'],2)}

TP: {round(signal['tp'],2)}
"""

                print(msg)

                send_telegram(msg)

        except Exception as e:

            print("Error:",e)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    run()
