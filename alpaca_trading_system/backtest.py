from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from alpaca_trading_system.config import AppConfig
from alpaca_trading_system.metrics import drawdown, performance_metrics
from alpaca_trading_system.risk import Position, target_orders
from alpaca_trading_system.strategy import generate_signals


@dataclass
class BacktestOutput:
    equity: pd.Series
    orders: pd.DataFrame
    trades: pd.DataFrame
    signals: pd.DataFrame
    metrics: dict[str, float]


def run_backtest(bars: pd.DataFrame, config: AppConfig) -> BacktestOutput:
    signals = generate_signals(bars, config.strategy)
    close_table = bars.pivot(index="timestamp", columns="symbol", values="close").sort_index()
    cash = config.risk.initial_capital
    positions: dict[str, Position] = {}
    equity_rows = []
    order_rows = []
    trade_rows = []

    for timestamp in close_table.index:
        prices = close_table.loc[timestamp].dropna()
        current_signals = signals[signals["timestamp"] == timestamp]
        for symbol, position in list(positions.items()):
            if symbol in prices:
                positions[symbol] = Position(symbol, position.quantity, position.avg_entry_price, float(prices[symbol]))

        equity_value = cash + sum(pos.notional for pos in positions.values())
        orders = target_orders(current_signals, positions, cash, config.risk)
        for order in orders:
            symbol = order["symbol"]
            if symbol not in prices:
                continue
            price = float(prices[symbol])
            qty = float(order["quantity"])
            if order["side"] == "buy":
                cost = qty * price
                if cost > cash:
                    continue
                cash -= cost
                positions[symbol] = Position(symbol, qty, price, price)
            else:
                position = positions.pop(symbol, None)
                if position is None:
                    continue
                proceeds = position.quantity * price
                cash += proceeds
                trade_rows.append(
                    {
                        "timestamp": timestamp,
                        "symbol": symbol,
                        "quantity": position.quantity,
                        "entry_price": position.avg_entry_price,
                        "exit_price": price,
                        "pnl": proceeds - position.quantity * position.avg_entry_price,
                        "reason": order["reason"],
                    }
                )
            order_rows.append({"timestamp": timestamp, "price": price, **order})
        equity_value = cash + sum(pos.notional for pos in positions.values())
        equity_rows.append({"timestamp": timestamp, "equity": equity_value, "cash": cash, "positions": len(positions)})

    equity_df = pd.DataFrame(equity_rows).set_index("timestamp")
    equity = equity_df["equity"]
    returns = equity.pct_change().fillna(0)
    orders_df = pd.DataFrame(order_rows)
    trades_df = pd.DataFrame(trade_rows)
    metrics = performance_metrics(equity, returns, trades_df)
    return BacktestOutput(equity, orders_df, trades_df, signals, metrics)


def save_backtest_output(output: BacktestOutput, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([output.metrics]).to_csv(output_dir / "metrics.csv", index=False)
    output.equity.to_csv(output_dir / "equity_curve.csv")
    output.orders.to_csv(output_dir / "orders.csv", index=False)
    output.trades.to_csv(output_dir / "trades.csv", index=False)
    output.signals.to_csv(output_dir / "signals.csv", index=False)
    _save_equity_chart(output.equity, output_dir / "equity_curve.png")
    _save_drawdown_chart(output.equity, output_dir / "drawdown.png")


def _save_equity_chart(equity: pd.Series, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(equity.index, equity)
    ax.set_title("Portfolio Equity Curve")
    ax.set_ylabel("Portfolio Value ($)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _save_drawdown_chart(equity: pd.Series, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(equity.index, drawdown(equity) * 100)
    ax.set_title("Portfolio Drawdown")
    ax.set_ylabel("Drawdown (%)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
