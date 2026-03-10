import requests
import pandas as pd
import numpy as np
import time
from config import *

# ==============================
# TELEGRAM
# ==============================

def send_telegram(msg):

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }

    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Telegram error:", e)


# ==============================
# GET GOLD DATA
# ==============================

def get_gold_data():

    url = "https://www.alphavantage.co/query"

    params = {
        "function": "FX_INTRADAY",
        "from_symbol": SYMBOL,
        "to_symbol": MARKET,
        "interval": "5min",
        "apikey": ALPHA_API_KEY,
        "outputsize": "compact"
    }

    r = requests.get(url, params=params)

    data = r.json()

    key = "Time Series FX (5min)"

    if key not in data:
        print("API ERROR:", data)
        return None

    candles = data[key]

    df = pd.DataFrame(candles).T

    df.columns = ["open","high","low","close"]

    df = df.astype(float)

    df = df.sort_index()

    return df


# ==============================
# INDICATORS
# ==============================

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


# ==============================
# ANALYZE
# ==============================

def analyze(df):

    last = df.iloc[-1]

    price = last["close"]

    trend = "neutral"

    if last["ema20"] > last["ema50"]:
        trend = "bullish"

    if last["ema20"] < last["ema50"]:
        trend = "bearish"

    rsi = last["rsi"]

    if trend == "bullish" and rsi < 65:

        entry = price
        sl = price - 2
        tp = price + 4

        return {
            "type":"BUY",
            "entry":entry,
            "sl":sl,
            "tp":tp
        }

    if trend == "bearish" and rsi > 35:

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


# ==============================
# MAIN LOOP
# ==============================

def run():

    print("BOT VÀNG ĐÃ CHẠY")

    while True:

        try:

            df = get_gold_data()

            if df is None:
                time.sleep(60)
                continue

            df = indicators(df)

            signal = analyze(df)

            if signal:

                msg = f"""
<b>GOLD SIGNAL</b>

Type: {signal['type']}

Entry: {round(signal['entry'],2)}

SL: {round(signal['sl'],2)}

TP: {round(signal['tp'],2)}
"""

                print(msg)

                send_telegram(msg)

        except Exception as e:

            print("Error:", e)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    run()
