import requests
from config.upstox_config import ACCESS_TOKEN_FILE

with open(ACCESS_TOKEN_FILE) as f:
    token = f.read().strip()

headers = {
    "Authorization": f"Bearer {token}",
    "accept": "application/json"
}

url = "https://api.upstox.com/v2/user/profile"

resp = requests.get(url, headers=headers)

print("STATUS:", resp.status_code)
print(resp.text)
