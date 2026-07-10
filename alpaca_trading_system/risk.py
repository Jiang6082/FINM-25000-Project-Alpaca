from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from alpaca_trading_system.config import RiskConfig


@dataclass(frozen=True)
class Position:
    symbol: str
    quantity: float
    avg_entry_price: float
    market_price: float

    @property
    def notional(self) -> float:
        return self.quantity * self.market_price

    @property
    def unrealized_return(self) -> float:
        if self.avg_entry_price == 0:
            return 0.0
        return self.market_price / self.avg_entry_price - 1


def target_orders(
    latest_signal: pd.DataFrame,
    positions: dict[str, Position],
    cash: float,
    config: RiskConfig,
) -> list[dict]:
    """Translate desired signals into risk-checked target orders.

    Exits are generated first: a position is closed when it drops out of the
    signal ranking or hits its stop-loss/take-profit level. New entries are
    then sized so that total exposure (positions kept open plus new buys)
    stays within ``max_total_notional``, and never exceeds available cash
    unless leverage is explicitly allowed. The system is structurally
    long-only: sells only ever close existing long positions.
    """
    orders: list[dict] = []
    active_signals = latest_signal[latest_signal["signal"] == 1].sort_values("score", ascending=False)
    desired = set(active_signals.head(config.max_open_positions)["symbol"])

    exited: set[str] = set()
    for symbol, position in positions.items():
        if (
            symbol not in desired
            or position.unrealized_return <= -config.stop_loss_pct
            or position.unrealized_return >= config.take_profit_pct
        ):
            orders.append({"symbol": symbol, "side": "sell", "quantity": position.quantity, "reason": "exit"})
            exited.add(symbol)

    held = {symbol: position for symbol, position in positions.items() if symbol not in exited}
    held_exposure = sum(position.notional for position in held.values())
    total_budget = max(config.max_total_notional - held_exposure, 0.0)
    if not config.allow_leverage:
        total_budget = min(total_budget, max(cash, 0.0))

    # Symbols exited this cycle (e.g. on stop-loss) are not re-entered in the
    # same cycle; they become eligible again on the next evaluation.
    slots = max(config.max_open_positions - len(held), 0)
    candidates = [
        row
        for _, row in active_signals.iterrows()
        if row["symbol"] not in held and row["symbol"] not in exited
    ][:slots]
    if not candidates or total_budget <= 0:
        return orders

    per_position = min(config.max_position_notional, total_budget / len(candidates))
    remaining_budget = total_budget
    for row in candidates:
        price = float(row["close"])
        quantity = int(min(per_position, remaining_budget) // price)
        if quantity <= 0:
            continue
        orders.append({"symbol": row["symbol"], "side": "buy", "quantity": quantity, "reason": "entry"})
        remaining_budget -= quantity * price
    return orders
