from __future__ import annotations

import numpy as np
import pandas as pd


TRADING_DAYS = 252


def drawdown(equity: pd.Series) -> pd.Series:
    return equity / equity.cummax() - 1


def performance_metrics(equity: pd.Series, daily_returns: pd.Series, trades: pd.DataFrame) -> dict[str, float]:
    years = max((equity.index[-1] - equity.index[0]).days / 365.25, 1 / TRADING_DAYS)
    total_return = equity.iloc[-1] / equity.iloc[0] - 1
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1
    volatility = daily_returns.std(ddof=0) * np.sqrt(TRADING_DAYS)
    sharpe = daily_returns.mean() * TRADING_DAYS / volatility if volatility > 0 else 0.0
    downside = daily_returns[daily_returns < 0].std(ddof=0) * np.sqrt(TRADING_DAYS)
    sortino = daily_returns.mean() * TRADING_DAYS / downside if downside > 0 else 0.0
    hit_rate = float((trades["pnl"] > 0).mean()) if len(trades) else 0.0
    return {
        "total_return": float(total_return),
        "cagr": float(cagr),
        "volatility": float(volatility),
        "sharpe": float(sharpe),
        "sortino": float(sortino),
        "max_drawdown": float(drawdown(equity).min()),
        "num_trades": float(len(trades)),
        "hit_rate": hit_rate,
    }
