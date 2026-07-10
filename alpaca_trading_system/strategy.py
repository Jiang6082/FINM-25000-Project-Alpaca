from __future__ import annotations

import numpy as np
import pandas as pd

from alpaca_trading_system.config import StrategyConfig


def compute_indicators(bars: pd.DataFrame, config: StrategyConfig) -> pd.DataFrame:
    """Compute trend, breakout, and volatility features for every symbol."""
    rows = []
    for symbol, data in bars.groupby("symbol"):
        frame = data.sort_values("timestamp").copy()
        close = frame["close"]
        frame["fast_sma"] = close.rolling(config.fast_window).mean()
        frame["slow_sma"] = close.rolling(config.slow_window).mean()
        frame["breakout_high"] = close.rolling(config.breakout_window).max().shift(1)
        frame["return_1d"] = close.pct_change()
        frame["momentum"] = close / close.shift(config.breakout_window) - 1
        frame["realized_vol"] = frame["return_1d"].rolling(config.volatility_window).std()
        frame["score"] = frame["momentum"] / frame["realized_vol"].replace(0, np.nan)
        frame["trend_ok"] = frame["fast_sma"] > frame["slow_sma"]
        frame["breakout_ok"] = close > frame["breakout_high"]
        rows.append(frame)
    return pd.concat(rows, ignore_index=True).sort_values(["timestamp", "symbol"])


def generate_signals(bars: pd.DataFrame, config: StrategyConfig) -> pd.DataFrame:
    """Generate long/flat signals from fully systematic rules."""
    data = compute_indicators(bars, config)
    data["raw_signal"] = (data["trend_ok"] & data["breakout_ok"] & (data["score"] > 0)).astype(int)
    signal_frames = []
    for timestamp, day in data.groupby("timestamp"):
        active = day[day["raw_signal"] == 1].sort_values("score", ascending=False)
        selected_symbols = set(active.head(config.max_symbols)["symbol"])
        day = day.copy()
        day["signal"] = day["symbol"].isin(selected_symbols).astype(int)
        signal_frames.append(day)
    columns = [
        "timestamp",
        "symbol",
        "close",
        "fast_sma",
        "slow_sma",
        "momentum",
        "realized_vol",
        "score",
        "signal",
    ]
    return pd.concat(signal_frames, ignore_index=True)[columns]


def latest_signals(signals: pd.DataFrame) -> pd.DataFrame:
    latest_time = signals["timestamp"].max()
    return signals[signals["timestamp"] == latest_time].copy()
