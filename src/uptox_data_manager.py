import requests
import json
import time
import os
from config.upstox_config import ACCESS_TOKEN_FILE

# Load token
def load_access_token():
    if not os.path.exists(ACCESS_TOKEN_FILE):
        raise FileNotFoundError("❌ access_token.txt not found! Run token_generator first.")
    with open(ACCESS_TOKEN_FILE, "r") as f:
        return f.read().strip()


class UpstoxDataManager:
    BASE_URL = "https://api.upstox.com/v2"

    def __init__(self):
        self.access_token = load_access_token()
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "accept": "application/json"
        }
        print("✅ Upstox Data Manager initialized.")

    # ---------------------------
    # LIVE PRICE
    # ---------------------------
    def get_live_price(self, symbol: str):
        url = f"{self.BASE_URL}/market-quote/ltp?symbol={symbol}"

        try:
            resp = requests.get(url, headers=self.headers)
            data = resp.json()

            if "data" in data and symbol in data["data"]:
                return data["data"][symbol]["ltp"]

            return None
        except:
            return None

    # ---------------------------
    # HISTORICAL OHLC
    # ---------------------------
    def get_historical(self, symbol: str, interval="5minute", days=3):
        url = (
            f"{self.BASE_URL}/market/historical-candle?"
            f"instrument_key={symbol}"
            f"&interval={interval}"
            f"&to_date="
        )

        try:
            resp = requests.get(url, headers=self.headers)
            data = resp.json()

            if "data" in data and "candles" in data["data"]:
                return data["data"]["candles"]

            return []
        except:
            return []

    # ---------------------------
    # MARKET OPEN/CLOSE STATUS
    # ---------------------------
    def is_market_open(self):
        url = f"{self.BASE_URL}/market/status"

        try:
            resp = requests.get(url, headers=self.headers)
            data = resp.json()

            if "data" in data:
                return data["data"].get("market_open", False)

            return False
        except:
            return False
