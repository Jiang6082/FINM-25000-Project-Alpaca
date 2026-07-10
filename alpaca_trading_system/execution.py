from __future__ import annotations

from dataclasses import dataclass
import logging

from alpaca_trading_system.data import load_alpaca_keys


log = logging.getLogger(__name__)


@dataclass(frozen=True)
class OrderResult:
    symbol: str
    side: str
    quantity: float
    status: str
    order_id: str | None
    dry_run: bool


class PaperBroker:
    """Alpaca execution layer. The TradingClient is always paper=True."""

    def __init__(self) -> None:
        from alpaca.trading.client import TradingClient

        api_key, secret_key = load_alpaca_keys()
        self.client = TradingClient(api_key, secret_key, paper=True)

    def get_positions(self):
        return self.client.get_all_positions()

    def submit_market_order(self, symbol: str, side: str, quantity: float, dry_run: bool = True) -> OrderResult:
        if dry_run:
            log.info("DRY RUN order: %s %s x %s", side.upper(), quantity, symbol)
            return OrderResult(symbol, side, quantity, "dry_run", None, True)

        from alpaca.trading.enums import OrderSide, TimeInForce
        from alpaca.trading.requests import MarketOrderRequest

        request = MarketOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )
        order = self.client.submit_order(request)
        return OrderResult(symbol, side, quantity, str(order.status), str(order.id), False)


class SimulatedBroker:
    def submit_market_order(self, symbol: str, side: str, quantity: float, dry_run: bool = True) -> OrderResult:
        return OrderResult(symbol, side, quantity, "simulated", None, True)
