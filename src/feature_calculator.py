# src/feature_calculator.py

import numpy as np
import pandas as pd
from typing import List, Optional, Dict

class LiveFeatureCalculator:
    """Calculate v3 features on live data (same as your training)."""

    def __init__(self, feature_cols: List[str]):
        self.feature_cols = feature_cols

    def calculate(self, df: pd.DataFrame) -> Optional[Dict]:
        """Calculate features from dataframe."""

        if len(df) < 100:
            return None

        try:
            # Ensure numeric
            for col in ['close', 'high', 'low', 'open', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # ATR
            tr = pd.concat([
                df['high'] - df['low'],
                (df['high'] - df['close'].shift(1)).abs(),
                (df['low'] - df['close'].shift(1)).abs()
            ], axis=1).max(axis=1)
            df['atr_14'] = tr.rolling(14).mean()
            df['atr_pct'] = (df['atr_14'] / df['close']) * 100

            # RSI
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / (loss + 1e-10)
            df['rsi'] = 100 - (100 / (1 + rs))
            df['rsi_slope'] = df['rsi'].diff(1)

            # EMAs
            df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
            df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
            df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()

            # Returns / context
            df['idx_ret'] = np.log(df['close'] / df['close'].shift(1))
            df['idx_ret_3'] = df['idx_ret'].rolling(3).sum()
            df['excess_ret'] = 0
            df['excess_ret_ema3'] = 0
            df['rolling_beta'] = 1.0

            atr_mean = df['atr_pct'].rolling(100).mean()
            atr_std = df['atr_pct'].rolling(100).std()
            df['atrpct_z'] = (df['atr_pct'] - atr_mean) / (atr_std + 1e-6)
            df['atrpct_slope'] = df['atr_pct'].diff(5)
            df['atrpct_accel'] = df['atrpct_slope'].diff(5)

            # Time-of-day features (same style as your original)
            df['tod_fraction'] = (df.index % 75) / 75
            df['tod_sin'] = np.sin(2 * np.pi * df['tod_fraction'])
            df['tod_cos'] = np.cos(2 * np.pi * df['tod_fraction'])

            typical = (df['high'] + df['low'] + df['close']) / 3
            df['vwap_20'] = (typical * df['volume']).rolling(20).sum() / df['volume'].rolling(20).sum()
            df['vwap_dist'] = (df['close'] - df['vwap_20']) / (df['vwap_20'] + 1e-6)
            df['vwap_dist_change'] = df['vwap_dist'].diff(1)

            vol_mean = df['volume'].rolling(20).mean()
            vol_std = df['volume'].rolling(20).std()
            df['vol_zscore'] = (df['volume'] - vol_mean) / (vol_std + 1e-6)
            df['vol_ratio'] = df['volume'] / (vol_mean + 1e-6)
            df['vol_trend'] = df['vol_ratio'].ewm(span=10, adjust=False).mean() - 1

            df['ema_div'] = (df['ema_21'] - df['ema_50']) / (df['close'] + 1e-6)
            ema_div_mean = df['ema_div'].rolling(100).mean()
            ema_div_std = df['ema_div'].rolling(100).std()
            df['ema_div_z'] = (df['ema_div'] - ema_div_mean) / (ema_div_std + 1e-6)
            df['trend_regime'] = df['ema_div_z'] * np.sign(df['ema_21'] - df['ema_50'])

            numerator = (df['close'] - df['low']) - (df['high'] - df['close'])
            denominator = df['high'] - df['low'] + 1e-6
            df['clv'] = numerator / denominator
            df['clv_sum3'] = df['clv'].rolling(3).sum()

            df['volume_ratio'] = df['vol_ratio']
            df['volume_momentum'] = (
                df['volume'] - df['volume'].ewm(span=9, adjust=False).mean()
            ) / (df['volume'].ewm(span=9, adjust=False).mean() + 1e-6)

            df['bar_range'] = (df['high'] - df['low']) / (df['close'] + 1e-6)
            df['bar_body'] = (df['close'] - df['open']).abs() / (df['close'] + 1e-6)
            df['upper_wick'] = (
                df['high'] - df[['open', 'close']].max(axis=1)
            ) / (df['close'] + 1e-6)
            df['lower_wick'] = (
                df[['open', 'close']].min(axis=1) - df['low']
            ) / (df['close'] + 1e-6)

            # Latest row → feature dict
            latest = df.iloc[-1]
            features = {}
            for col in self.feature_cols:
                val = latest.get(col, 0)
                if np.isnan(val) or np.isinf(val):
                    val = 0
                features[col] = val

            return features

        except Exception as e:
            print(f"  ✗ Feature calculation error: {e}")
            return None
