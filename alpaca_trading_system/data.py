from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
import os
from pathlib import Path
import time

import numpy as np
import pandas as pd
from dotenv import load_dotenv


log = logging.getLogger(__name__)

BAR_COLUMNS = ["timestamp", "symbol", "open", "high", "low", "close", "volume"]


class MissingAlpacaCredentials(RuntimeError):
    pass


def load_alpaca_keys() -> tuple[str, str]:
    load_dotenv()
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    if not api_key or not secret_key:
        raise MissingAlpacaCredentials(
            "Missing ALPACA_API_KEY or ALPACA_SECRET_KEY. Add paper credentials to .env."
        )
    return api_key, secret_key


class AlpacaMarketData:
    """Alpaca market data provider for historical/recent OHLCV bars."""

    def __init__(self, feed: str = "iex") -> None:
        from alpaca.data.enums import DataFeed
        from alpaca.data.historical import StockHistoricalDataClient

        api_key, secret_key = load_alpaca_keys()
        self.client = StockHistoricalDataClient(api_key, secret_key)
        self.feed = DataFeed.IEX if feed.lower() == "iex" else DataFeed.SIP

    def fetch_bars(
        self,
        symbols: list[str],
        lookback_days: int = 252,
        timeframe: str = "day",
    ) -> pd.DataFrame:
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame

        frame = TimeFrame.Day if timeframe == "day" else TimeFrame.Minute
        end = datetime.now(timezone.utc)
        if timeframe == "day":
            start = end - timedelta(days=max(lookback_days + 10, 30))
        else:
            start = end - timedelta(days=max(lookback_days, 1))
        request = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=frame,
            start=start,
            end=end,
            feed=self.feed,
        )
        bars = self._fetch_with_retry(request).df
        if bars.empty:
            return pd.DataFrame(columns=BAR_COLUMNS)
        bars = bars.reset_index()
        return bars[BAR_COLUMNS].sort_values(["symbol", "timestamp"]).reset_index(drop=True)

    def _fetch_with_retry(self, request, attempts: int = 3, backoff_seconds: float = 2.0):
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                return self.client.get_stock_bars(request)
            except Exception as exc:
                last_error = exc
                log.warning("Market data fetch failed (attempt %s/%s): %s", attempt, attempts, exc)
                if attempt < attempts:
                    time.sleep(backoff_seconds * attempt)
        raise RuntimeError(
            f"Failed to fetch bars from Alpaca after {attempts} attempts: {last_error}"
        ) from last_error


class SimulatedMarketData:
    """Deterministic simulated OHLCV data for demos, tests, and no-key backtests."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed

    def fetch_bars(self, symbols: list[str], lookback_days: int = 252, timeframe: str = "day") -> pd.DataFrame:
        rng = np.random.default_rng(self.seed)
        dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=lookback_days, freq="B")
        frames = []
        for idx, symbol in enumerate(symbols):
            drift = 0.0002 + idx * 0.00005
            vol = 0.012 + idx * 0.001
            returns = rng.normal(drift, vol, len(dates))
            close = (100 + idx * 20) * np.exp(np.cumsum(returns))
            open_ = close * (1 + rng.normal(0, 0.002, len(dates)))
            high = np.maximum(open_, close) * (1 + rng.uniform(0.001, 0.012, len(dates)))
            low = np.minimum(open_, close) * (1 - rng.uniform(0.001, 0.012, len(dates)))
            volume = rng.integers(1_000_000, 8_000_000, len(dates))
            frames.append(
                pd.DataFrame(
                    {
                        "timestamp": dates,
                        "symbol": symbol,
                        "open": open_,
                        "high": high,
                        "low": low,
                        "close": close,
                        "volume": volume,
                    }
                )
            )
        return pd.concat(frames, ignore_index=True)


def append_bar_log(bars: pd.DataFrame, data_dir: Path) -> Path:
    """Append bars to today's log file, de-duplicated on (timestamp, symbol)."""
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / f"bars_{pd.Timestamp.now(tz='UTC').date()}.csv"
    combined = bars.copy()
    if path.exists():
        existing = pd.read_csv(path)
        combined = pd.concat([existing, combined], ignore_index=True)
    combined["timestamp"] = pd.to_datetime(combined["timestamp"], utc=True)
    combined = (
        combined.drop_duplicates(subset=["timestamp", "symbol"], keep="last")
        .sort_values(["symbol", "timestamp"])
        .reset_index(drop=True)
    )
    combined.to_csv(path, index=False)
    log.info("Logged %s bars (%s total today) to %s", len(bars), len(combined), path)
    return path


def pivot_close(bars: pd.DataFrame) -> pd.DataFrame:
    return bars.pivot(index="timestamp", columns="symbol", values="close").sort_index()
