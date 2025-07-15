import threading
import time
import requests
from datetime import datetime
import pytz
from flask import Flask
from telegram import Bot

# --- CONFIG ---
ODDS_API_KEY = "72c9b4a891ab427ecfc55777f7110a8c"
TELEGRAM_BOT_TOKEN = "7692195219:AAHbR-7wZFcDK1t9GFj_I2gn_4J2_hCKp7A"
TELEGRAM_CHAT_ID = "1205297695"
SPORT = "soccer"
REGIONS = "eu,uk,us"
MARKETS = "totals"
ODDS_API_URL = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds/"
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Used to track old odds
previous_odds = {}

# Flask server to keep Render alive
app = Flask(__name__)

@app.route('/')
def home():
    return '⚽ Trending Odds Bot is Running!'

def send_telegram(message):
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="HTML")

def fetch_odds():
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": "decimal"
    }
    try:
        response = requests.get(ODDS_API_URL, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        send_telegram(f"❌ Error fetching odds: {e}")
        return []

def process_odds(data):
    trending = []
    for match in data:
        match_id = match['id']
        start_time_utc = datetime.fromisoformat(match['commence_time'].replace("Z", "+00:00"))
        local_time = start_time_utc.astimezone(pytz.timezone("Europe/Amsterdam"))
        kickoff = local_time.strftime('%Y-%m-%d %H:%M')

        teams = f"{match['home_team']} vs {match['away_team']}"

        for bookmaker in match.get('bookmakers', []):
            for market in bookmaker.get('markets', []):
                if market['key'] == "totals":
                    for outcome in market['outcomes']:
                        if outcome['name'] == "Over":
                            point = outcome.get('point')
                            current_price = outcome['price']
                            odds_key = f"{match_id}_{point}"

                            if odds_key in previous_odds:
                                old_price = previous_odds[odds_key]
                                drop = old_price - current_price
                                if drop >= 0.25:
                                    trending.append({
                                        "match": teams,
                                        "kickoff": kickoff,
                                        "market": f"Over {point} Goals",
                                        "drop": f"{old_price} → {current_price}",
                                        "bookmaker": bookmaker['title']
                                    })

                            previous_odds[odds_key] = current_price
    return trending

def scan_loop():
    while True:
        data = fetch_odds()
        trending = process_odds(data)
        if trending:
            for item in trending:
                message = (
                    f"🔥 <b>Trending Match Alert</b>\n\n"
                    f"🏟️ <b>{item['match']}</b>\n"
                    f"🕘 Kickoff: {item['kickoff']}\n"
                    f"📉 Market: {item['market']}\n"
                    f"📊 Odds dropped: {item['drop']} ({item['bookmaker']})\n\n"
                    f"📈 High betting interest detected!"
                )
                send_telegram(message)
        time.sleep(60)

# Run Flask app + background scanner
if __name__ == '__main__':
    threading.Thread(target=scan_loop).start()
    app.run(host='0.0.0.0', port=10000)
