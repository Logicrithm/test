from src.data_manager import UpstoxDataManager

dm = UpstoxDataManager()
symbol = "NSE_EQ|RELIANCE"

print("\n📌 LIVE PRICE:")
print(dm.get_live_price(symbol))

print("\n📌 HISTORICAL (5m):")
print(dm.get_historical(symbol, "5minute", 1)[:3])

print("\n📌 MARKET OPEN?:")
print(dm.is_market_open(symbol))
