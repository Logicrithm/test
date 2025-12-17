import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

API_KEY = "5846aa74-42e5-4eaa-8c11-e80bc4176f9f"
API_SECRET = "4f34d1w5fb"
REDIRECT_URI = "http://127.0.0.1:5000/upstox/callback"
ACCESS_TOKEN_FILE = os.path.join(BASE_DIR, "access_token.txt")