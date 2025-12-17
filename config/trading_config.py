# config/trading_config.py

from pathlib import Path
import json

# Base directory = project root
BASE_DIR = Path(__file__).resolve().parent.parent

# === MODEL PATH ===
# Put your existing model here: models/model_v3_20251103.pkl
MODEL_PATH = BASE_DIR / "models" / "model_v3_20251103.pkl"

# === SYMBOLS ===

# Try to load recommended symbols if file exists (optional)
RECOMMENDED_FILE = BASE_DIR / "symbol_class.json"  # or adjust if needed

DEFAULT_SYMBOLS = [
    'SHRIRAMFIN', 'BEL', 'LT', 'TRENT', 'ADANIPORTS',
    'ADANIENT', 'BHARTIARTL', 'INDUSINDBK', 'DRREDDY', 'HEROMOTOCO'
]

try:
    with open(BASE_DIR / "phase1_results" / "recommended_symbols.json", "r") as f:
        recommended = json.load(f)
        TRADING_SYMBOLS = recommended.get("recommended_symbols", DEFAULT_SYMBOLS)[:10]
except Exception:
    TRADING_SYMBOLS = DEFAULT_SYMBOLS

# === RISK PROFILE ===
# 'conservative', 'balanced', 'aggressive'
RISK_PROFILE = "aggressive"

# === TRADING PARAMETERS ===
BASE_TRADING_PARAMS = {
    'conf_threshold': 0.55,
    'cost_pct': 0.10,
    'max_trades_per_symbol': 2,
    'max_total_positions': 8,
    'position_size': 10000,
    'stop_loss_atr_mult': 2.0,
    'take_profit_pct': 0.40,
    'time_stop_minutes': 60,
    'min_atr_pct': 0.6,
}

TRADING_PARAM_OVERRIDES = {
    'conservative': {
        'conf_threshold': 0.62,
        'max_total_positions': 5,
        'position_size': 8000,
        'stop_loss_atr_mult': 1.8,
        'take_profit_pct': 0.30,
        'time_stop_minutes': 45,
        'min_atr_pct': 0.8,
    },
    'aggressive': {
        'conf_threshold': 0.48,
        'max_trades_per_symbol': 3,
        'max_total_positions': 12,
        'position_size': 15000,
        'stop_loss_atr_mult': 2.5,
        'take_profit_pct': 0.60,
        'time_stop_minutes': 90,
        'min_atr_pct': 0.4,
    }
}

TRADING_PARAMS = {
    **BASE_TRADING_PARAMS,
    **TRADING_PARAM_OVERRIDES.get(RISK_PROFILE, {})
}

# === TRADING HOURS (IST) ===
TRADING_HOURS = {
    'market_open': '09:15',
    'trading_start': '09:25',
    'trading_end': '15:20',
    'market_close': '15:30'
}

# === RISK LIMITS ===
BASE_RISK_LIMITS = {
    'max_daily_loss': -1000,
    'max_daily_trades': 20,
    'cooldown_after_loss_minutes': 15
}

RISK_LIMIT_OVERRIDES = {
    'conservative': {
        'max_daily_loss': -600,
        'max_daily_trades': 12,
        'cooldown_after_loss_minutes': 20,
    },
    'aggressive': {
        'max_daily_loss': -2000,
        'max_daily_trades': 30,
        'cooldown_after_loss_minutes': 5,
    }
}

RISK_LIMITS = {
    **BASE_RISK_LIMITS,
    **RISK_LIMIT_OVERRIDES.get(RISK_PROFILE, {})
}

# === LOGS DIR ===
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
