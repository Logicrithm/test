# src/paper_trader.py

import pickle
import numpy as np
import pandas as pd
from datetime import datetime
import time
from typing import List

from config.trading_config import (
    MODEL_PATH, LOGS_DIR, TRADING_SYMBOLS, RISK_PROFILE,
    TRADING_PARAMS, TRADING_HOURS, RISK_LIMITS
)
from src.upstox_data_manager import UpstoxDataManager
from src.feature_calculator import LiveFeatureCalculator
from src.position_manager import Position


class LivePaperTrader:
    """Live 5m paper trading using Upstox data + your ML model."""

    def __init__(self, access_token: str):
        print("=" * 70)
        print("LIVE PAPER TRADER - UPSTOX INTEGRATION")
        print("=" * 70)

        # Load model
        print("\nLoading model...")
        with open(MODEL_PATH, "rb") as f:
            model_data = pickle.load(f)
            self.model = model_data['model']
            self.feature_cols = model_data['feature_cols']
        print(f"✓ Model loaded with {len(self.feature_cols)} features")

        # Data + features
        self.data_manager = UpstoxDataManager(access_token)
        self.feature_calc = LiveFeatureCalculator(self.feature_cols)

        # State
        self.active_positions: List[Position] = []
        self.closed_trades: List[Position] = []
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        self.trade_count_today = 0
        self.last_loss_time = None

        # Logs
        self.trades_log = LOGS_DIR / f"live_trades_{datetime.now():%Y%m%d}.csv"

        print(f"✓ Trading {len(TRADING_SYMBOLS)} symbols")
        print(f"✓ Risk profile: {RISK_PROFILE.capitalize()} "
              f"(conf≥{TRADING_PARAMS['conf_threshold']:.2f}, "
              f"positions≤{TRADING_PARAMS['max_total_positions']}, "
              f"size ₹{TRADING_PARAMS['position_size']})")
        print(f"✓ Logs: {self.trades_log.name}")
        print("=" * 70)

    def is_trading_hours(self) -> bool:
        now_str = datetime.now().strftime('%H:%M')
        return TRADING_HOURS['trading_start'] <= now_str <= TRADING_HOURS['trading_end']

    def check_risk_limits(self) -> bool:
        if self.daily_pnl <= RISK_LIMITS['max_daily_loss']:
            print(f"⚠ Daily loss limit reached: ₹{self.daily_pnl:.2f}")
            return False

        if self.trade_count_today >= RISK_LIMITS['max_daily_trades']:
            print(f"⚠ Daily trade limit reached: {self.trade_count_today}")
            return False

        if self.last_loss_time:
            mins = (datetime.now() - self.last_loss_time).total_seconds() / 60
            if mins < RISK_LIMITS['cooldown_after_loss_minutes']:
                return False

        return True

    def log_trade(self, position: Position):
        row = pd.DataFrame([position.to_dict()])
        if self.trades_log.exists():
            row.to_csv(self.trades_log, mode='a', header=False, index=False)
        else:
            row.to_csv(self.trades_log, index=False)

    def process_symbol(self, symbol: str):
        current_time = datetime.now()

        # Get latest bar
        bar = self.data_manager.get_current_bar(symbol)
        if not bar:
            return

        current_price = float(bar['close'])
        high = float(bar['high'])
        low = float(bar['low'])

        # 1) Check exits
        for pos in self.active_positions[:]:
            if pos.symbol == symbol:
                if pos.check_exit(current_price, high, low, current_time):
                    self.active_positions.remove(pos)
                    self.closed_trades.append(pos)
                    self.daily_pnl += pos.pnl
                    self.total_pnl += pos.pnl

                    if pos.pnl < 0:
                        self.last_loss_time = current_time

                    print(f"  [{current_time:%H:%M}] {symbol}: "
                          f"{pos.exit_reason.upper()} @ ₹{pos.exit_price:.2f} | "
                          f"P&L: ₹{pos.pnl:+.2f}")
                    self.log_trade(pos)

        # 2) Check if new entry allowed
        if not self.check_risk_limits():
            return

        if len(self.active_positions) >= TRADING_PARAMS['max_total_positions']:
            return

        symbol_positions = sum(1 for p in self.active_positions if p.symbol == symbol)
        if symbol_positions >= TRADING_PARAMS['max_trades_per_symbol']:
            return

        # 3) Get history + features
        df = self.data_manager.get_latest_bars(symbol, n_bars=200)
        if df.empty:
            return

        features = self.feature_calc.calculate(df)
        if not features:
            return

        atr_pct = features.get('atr_pct', 1.0)
        if atr_pct < TRADING_PARAMS['min_atr_pct']:
            return

        # 4) Predict
        X = np.array([[features[col] for col in self.feature_cols]])
        X = np.nan_to_num(X, nan=0.0)
        pred_proba = float(self.model.predict(X)[0])

        if pred_proba >= TRADING_PARAMS['conf_threshold']:
            pos = Position(
                symbol=symbol,
                entry_price=current_price,
                entry_time=current_time,
                confidence=pred_proba,
                atr_pct=atr_pct
            )
            self.active_positions.append(pos)
            self.trade_count_today += 1

            print(f"  [{current_time:%H:%M}] {symbol}: "
                  f"ENTRY @ ₹{pos.entry_price:.2f} | "
                  f"Conf: {pos.confidence:.2%} | "
                  f"TP: ₹{pos.take_profit:.2f} | SL: ₹{pos.stop_loss:.2f}")

    def print_status(self):
        print(f"\n[{datetime.now():%H:%M:%S}] Status:"
              f" Active: {len(self.active_positions)} | "
              f"Trades today: {self.trade_count_today} | "
              f"Daily P&L: ₹{self.daily_pnl:+.2f}")

    def end_of_day(self):
        print("\n" + "=" * 70)
        print("END OF DAY SUMMARY")
        print("=" * 70)

        for pos in self.active_positions[:]:
            pos.exit_price = pos.entry_price
            pos.exit_reason = 'eod_close'
            pos.close(datetime.now())
            self.closed_trades.append(pos)
            self.log_trade(pos)

        if self.closed_trades:
            pnls = [t.pnl for t in self.closed_trades]
            wins = [p for p in pnls if p > 0]

            print(f"\nTrades: {len(pnls)}")
            print(f"Wins: {len(wins)} ({len(wins)/len(pnls)*100:.1f}%)")
            print(f"Total P&L: ₹{sum(pnls):+,.2f}")
            print(f"Avg P&L: ₹{np.mean(pnls):+.2f}")

            if wins and any(p < 0 for p in pnls):
                pf = sum(wins) / abs(sum([p for p in pnls if p < 0]))
                print(f"Profit Factor: {pf:.2f}")

        print("=" * 70)

    def run(self):
        print("\nStarting live paper trading...")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                now_str = datetime.now().strftime('%H:%M')

                # Auto end-of-day
                if now_str >= TRADING_HOURS['market_close']:
                    self.end_of_day()
                    break

                if not self.is_trading_hours():
                    time.sleep(60)
                    continue

                for symbol in TRADING_SYMBOLS:
                    try:
                        self.process_symbol(symbol)
                    except Exception as e:
                        print(f"  ✗ Error processing {symbol}: {e}")

                self.print_status()

                # Sleep roughly one 5m bar
                time.sleep(300)

        except KeyboardInterrupt:
            print("\n\n⚠ Stopping trading via KeyboardInterrupt...")
            self.end_of_day()
