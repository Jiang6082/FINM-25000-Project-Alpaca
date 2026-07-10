import pandas as pd

from alpaca_trading_system.config import load_config
from alpaca_trading_system.data import SimulatedMarketData
from alpaca_trading_system.strategy import generate_signals, latest_signals


def test_strategy_generates_long_flat_signals():
    config = load_config()
    bars = SimulatedMarketData(seed=7).fetch_bars(config.tickers, lookback_days=120)
    signals = generate_signals(bars, config.strategy)
    assert {"timestamp", "symbol", "score", "signal"}.issubset(signals.columns)
    assert set(signals["signal"].dropna().unique()).issubset({0, 1})
    latest = latest_signals(signals)
    assert len(latest) == len(config.tickers)
    assert pd.api.types.is_numeric_dtype(signals["score"])
