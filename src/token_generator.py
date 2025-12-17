import webbrowser
import requests
from flask import Flask, request
from config.upstox_config import (
    API_KEY,
    API_SECRET,
    REDIRECT_URI,
    ACCESS_TOKEN_FILE
)

app = Flask(__name__)

AUTH_URL = (
    "https://api.upstox.com/v2/login/authorization/dialog"
    f"?response_type=code&client_id={API_KEY}&redirect_uri={REDIRECT_URI}"
)

@app.route("/")
def index():
    return "Upstox OAuth Token Generator Running"

@app.route("/upstox/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "No authorization code received"

    print("AUTH CODE:", code)

    token_url = "https://api.upstox.com/v2/login/authorization/token"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "accept": "application/json"
    }

    payload = {
        "code": code,
        "client_id": API_KEY,
        "client_secret": API_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    # 🚨 IMPORTANT: data=payload (NOT json=payload)
    response = requests.post(token_url, headers=headers, data=payload)
    resp_json = response.json()

    print("TOKEN RESPONSE:", resp_json)

    if resp_json.get("status") != "success":
        return f"❌ ERROR GETTING TOKEN: {resp_json}"

    access_token = resp_json["data"]["access_token"]

    with open(ACCESS_TOKEN_FILE, "w") as f:
        f.write(access_token)

    print("✅ REAL ACCESS TOKEN SAVED")
    return "✅ Access token generated successfully. You may close this window."

if __name__ == "__main__":
    print("\nOpening browser for Upstox login...\n")
    webbrowser.open(AUTH_URL)
    app.run(port=5000)
