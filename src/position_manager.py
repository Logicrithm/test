# src/position_manager.py

from datetime import datetime
from typing import Dict
from config.trading_config import TRADING_PARAMS

class Position:
    """Track open position and exit logic."""

    def __init__(self, symbol: str, entry_price: float, entry_time: datetime,
                 confidence: float, atr_pct: float):
        self.symbol = symbol
        self.entry_price = entry_price
        self.entry_time = entry_time
        self.confidence = confidence
        self.atr_pct = atr_pct

        self.stop_loss = entry_price * (
            1 - TRADING_PARAMS['stop_loss_atr_mult'] * atr_pct / 100
        )
        self.take_profit = entry_price * (
            1 + TRADING_PARAMS['take_profit_pct'] / 100
        )

        self.exit_price = None
        self.exit_time = None
        self.exit_reason = None
        self.pnl = None

    def check_exit(self, current_price: float, high: float, low: float,
                   current_time: datetime) -> bool:
        """Check if position should exit."""
        # SL
        if low <= self.stop_loss:
            self.exit_price = self.stop_loss
            self.exit_reason = 'stop_loss'
            self.close(current_time)
            return True

        # TP
        if high >= self.take_profit:
            self.exit_price = self.take_profit
            self.exit_reason = 'take_profit'
            self.close(current_time)
            return True

        # Time-based stop
        time_elapsed = (current_time - self.entry_time).total_seconds() / 60
        if time_elapsed >= TRADING_PARAMS['time_stop_minutes']:
            self.exit_price = current_price
            self.exit_reason = 'time_stop'
            self.close(current_time)
            return True

        return False

    def close(self, exit_time: datetime):
        """Finalize trade P&L."""
        self.exit_time = exit_time
        gross_ret = ((self.exit_price - self.entry_price) / self.entry_price) * 100
        net_ret = gross_ret - TRADING_PARAMS['cost_pct']
        self.pnl = net_ret * TRADING_PARAMS['position_size'] / 100

    def to_dict(self) -> Dict:
        """Convert to dict for logging."""
        return {
            'symbol': self.symbol,
            'entry_time': self.entry_time.strftime('%Y-%m-%d %H:%M:%S'),
            'entry_price': round(self.entry_price, 2),
            'exit_time': self.exit_time.strftime('%Y-%m-%d %H:%M:%S') if self.exit_time else None,
            'exit_price': round(self.exit_price, 2) if self.exit_price else None,
            'confidence': round(self.confidence, 4),
            'atr_pct': round(self.atr_pct, 4),
            'stop_loss': round(self.stop_loss, 2),
            'take_profit': round(self.take_profit, 2),
            'pnl': round(self.pnl, 2) if self.pnl else None,
            'exit_reason': self.exit_reason,
            'duration_minutes': (
                (self.exit_time - self.entry_time).total_seconds() / 60
                if self.exit_time else None
            )
        }
