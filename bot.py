import time
import requests
import pandas as pd
import ta
import math
import os
from telegram import Bot

# === ENV VARIABLES ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
bot = Bot(token=BOT_TOKEN)

# === CONFIG ===
SYMBOL = 'ETHUSDT'
INTERVAL = '1h'
LIMIT = 100
CHECK_EVERY = 300  # in seconds (5 minutes)

# === Binance Kline Fetch ===
def get_klines():
    url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval={INTERVAL}&limit={LIMIT}"
    data = requests.get(url).json()
    df = pd.DataFrame(data, columns=[
        "time", "open", "high", "low", "close", "volume",
        "_", "_", "_", "_", "_", "_"
    ])
    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["open"] = df["open"].astype(float)
    df["volume"] = df["volume"].astype(float)
    return df

# === Pattern Detection ===
def detect_patterns(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    pattern = None

    # Double Bottom
    if df["low"].iloc[-2] < df["low"].iloc[-3] and        df["low"].iloc[-2] == min(df["low"].tail(5)) and        last["low"] > df["low"].iloc[-2]:
        pattern = "🟢 Double Bottom"

    # Double Top
    elif df["high"].iloc[-2] > df["high"].iloc[-3] and          df["high"].iloc[-2] == max(df["high"].tail(5)) and          last["high"] < df["high"].iloc[-2]:
        pattern = "🔴 Double Top"

    # Head and Shoulders (very simple logic)
    elif df["high"].iloc[-4] < df["high"].iloc[-3] > df["high"].iloc[-2]:
        pattern = "🔴 Head & Shoulders"
    elif df["low"].iloc[-4] > df["low"].iloc[-3] < df["low"].iloc[-2]:
        pattern = "🟢 Inverse H&S"

    # Triangle Breakout (basic logic)
    if abs(df["high"].iloc[-1] - df["high"].iloc[-2]) < 5 and        df["low"].iloc[-1] > df["low"].iloc[-2]:
        pattern = "🟢 Ascending Triangle"

    elif abs(df["low"].iloc[-1] - df["low"].iloc[-2]) < 5 and          df["high"].iloc[-1] < df["high"].iloc[-2]:
        pattern = "🔴 Descending Triangle"

    return pattern

# === Technical Indicator Check ===
def analyze(df):
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd_diff()
    df['ema20'] = ta.trend.EMAIndicator(df['close'], window=20).ema_indicator()

    price = df['close'].iloc[-1]
    rsi = df['rsi'].iloc[-1]
    macd_hist = df['macd'].iloc[-1]
    ema = df['ema20'].iloc[-1]
    pattern = detect_patterns(df)

    signal = None

    # Breakout Logic
    if price > max(df["high"].iloc[-6:-1]) and rsi > 50 and macd_hist > 0:
        signal = "🚀 Breakout Detected!"

    # Pullback Logic
    elif abs(price - ema) / price < 0.01 and rsi < 40 and macd_hist < 0:
        signal = "📉 Pullback Detected!"

    return signal, pattern, price, rsi, macd_hist

# === Telegram Send ===
def send_telegram(text):
    bot.send_message(chat_id=CHAT_ID, text=text)

# === Main Loop ===
while True:
    try:
        df = get_klines()
        signal, pattern, price, rsi, macd = analyze(df)

        message = f"📊 ETH/USDT Market Update\nPrice: ${price:.2f}\nRSI: {rsi:.2f}\nMACD: {macd:.4f}"

        if signal:
            message += f"\n\n{signal}"
        if pattern:
            message += f"\n🧠 Pattern: {pattern}"

        if signal or pattern:
            send_telegram(message)

        print("Checked:", message)
    except Exception as e:
        print("Error:", e)

    time.sleep(CHECK_EVERY)