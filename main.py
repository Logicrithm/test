# main.py

from config.upstox_config import ACCESS_TOKEN_FILE
from src.paper_trader import LivePaperTrader

if __name__ == "__main__":
    with open(ACCESS_TOKEN_FILE, "r") as f:
        access_token = f.read().strip()

    trader = LivePaperTrader(access_token)
    trader.run()
