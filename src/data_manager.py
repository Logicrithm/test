import requests
import os
from datetime import datetime, timedelta
from config.upstox_config import ACCESS_TOKEN_FILE

def load_access_token():
    if not os.path.exists(ACCESS_TOKEN_FILE):
        raise FileNotFoundError("access_token.txt not found")
    with open(ACCESS_TOKEN_FILE, "r") as f:
        return f.read().strip()


class UpstoxDataManager:
    BASE_URL = "https://api.upstox.com/v2"

    def __init__(self):
        self.token = load_access_token()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "accept": "application/json",
            "Content-Type": "application/json"
        }
        print("✅ Upstox Data Manager initialized.")

    # -------------------------------------------------
    # LIVE LTP (CORRECT METHOD)
    # -------------------------------------------------
    def get_live_price(self, instrument_key: str):
        url = f"{self.BASE_URL}/market-quote/ltp"

        payload = {
            "instrument_key": [instrument_key]
        }

        resp = requests.post(url, headers=self.headers, json=payload).json()

        if "data" in resp and instrument_key in resp["data"]:
            return resp["data"][instrument_key]["ltp"]

        return None

    # -------------------------------------------------
    # HISTORICAL CANDLES (INTRADAY + DAILY)
    # -------------------------------------------------
    def get_historical(self, instrument_key: str, interval="5minute", days=3):
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)

        url = (
            f"{self.BASE_URL}/market/historical-candle"
            f"?instrument_key={instrument_key}"
            f"&interval={interval}"
            f"&from_date={from_date.strftime('%Y-%m-%d')}"
            f"&to_date={to_date.strftime('%Y-%m-%d')}"
        )

        resp = requests.get(url, headers=self.headers).json()

        if "data" in resp and "candles" in resp["data"]:
            return resp["data"]["candles"]

        return []

    # -------------------------------------------------
    # MARKET OPEN CHECK (PRACTICAL METHOD)
    # -------------------------------------------------
    def is_market_open(self, instrument_key="NSE_EQ|RELIANCE"):
        """
        Practical check: if LTP exists, market is open
        """
        ltp = self.get_live_price(instrument_key)
        return ltp is not None
