import os
import threading
import time
import requests
from flask import Flask
from telegram import Bot

# ====== CONFIG ======
TELEGRAM_BOT_TOKEN = "7692195219:AAHbR-7wZFcDK1t9GFj_I2gn_4J2_hCKp7A"
TELEGRAM_CHAT_ID = "1205297695"
ODDS_API_KEY = "72c9b4a891ab427ecfc55777f7110a8c"
CHECK_INTERVAL = 60  # seconds
# =====================

bot = Bot(token=TELEGRAM_BOT_TOKEN)
app = Flask(__name__)

def send_message(msg):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
        print(f"[✅] Sent to Telegram: {msg}")
    except Exception as e:
        print(f"[❌] Failed to send: {e}")

def scan_odds():
    while True:
        try:
            print("[⏳] Checking odds...")
            url = "https://api.the-odds-api.com/v4/sports/soccer/odds"
            params = {
                "regions": "eu",
                "markets": "totals",
                "oddsFormat": "decimal",
                "apiKey": ODDS_API_KEY
            }
            response = requests.get(url, params=params)
            data = response.json()

            count = 0
            for match in data:
                title = match.get("home_team", "") + " vs " + match.get("away_team", "")
                for bookmaker in match.get("bookmakers", []):
                    for market in bookmaker.get("markets", []):
                        if market["key"] == "totals":
                            for outcome in market["outcomes"]:
                                if outcome["point"] in [2.5, 3.5]:
                                    if outcome["price"] < 1.80:  # Just a dummy condition
                                        send_message(f"🔥 {title} has low odds ({outcome['price']}) for Over {outcome['point']}")
                                        count += 1
            print(f"[✓] Scan complete. {count} alerts sent.")
        except Exception as e:
            print(f"[ERROR] {e}")
        time.sleep(CHECK_INTERVAL)

@app.route("/")
def home():
    return "⚽ Trending Odds Bot is running!"

# Start scanner in thread
threading.Thread(target=scan_odds, daemon=True).start()

# Start Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
