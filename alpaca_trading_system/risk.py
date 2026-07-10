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
    """Translate desired signals into risk-checked target orders."""
    orders: list[dict] = []
    active_signals = latest_signal[latest_signal["signal"] == 1].sort_values("score", ascending=False)
    max_positions = min(config.max_open_positions, len(active_signals))
    max_total = min(config.max_total_notional, cash if not config.allow_leverage else config.max_total_notional)
    per_position = min(config.max_position_notional, max_total / max(max_positions, 1))
    desired = set(active_signals.head(max_positions)["symbol"])

    for symbol, position in positions.items():
        if (
            symbol not in desired
            or position.unrealized_return <= -config.stop_loss_pct
            or position.unrealized_return >= config.take_profit_pct
        ):
            orders.append({"symbol": symbol, "side": "sell", "quantity": position.quantity, "reason": "exit"})

    open_after_exits = {symbol for symbol in positions if symbol in desired}
    for _, row in active_signals.iterrows():
        symbol = row["symbol"]
        if symbol in open_after_exits:
            continue
        if len(open_after_exits) >= config.max_open_positions:
            continue
        price = float(row["close"])
        quantity = int(per_position // price)
        if quantity <= 0:
            continue
        orders.append({"symbol": symbol, "side": "buy", "quantity": quantity, "reason": "entry"})
        open_after_exits.add(symbol)

    if not config.allow_short:
        orders = [order for order in orders if order["side"] in {"buy", "sell"} and order["quantity"] > 0]
    return orders
