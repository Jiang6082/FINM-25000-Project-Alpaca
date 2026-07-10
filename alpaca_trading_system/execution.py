from __future__ import annotations

from dataclasses import dataclass, replace
import logging
import time

from alpaca_trading_system.data import load_alpaca_keys


log = logging.getLogger(__name__)

# Order states that will not change again; anything else is still open.
TERMINAL_STATUSES = {"filled", "canceled", "rejected", "expired"}


@dataclass(frozen=True)
class OrderResult:
    symbol: str
    side: str
    quantity: float
    status: str
    order_id: str | None
    dry_run: bool
    filled_quantity: float = 0.0
    filled_avg_price: float | None = None
    error: str | None = None


def _status_string(order) -> str:
    status = getattr(order.status, "value", order.status)
    return str(status).lower()


class PaperBroker:
    """Alpaca execution layer. The TradingClient is always paper=True."""

    def __init__(self) -> None:
        from alpaca.trading.client import TradingClient

        api_key, secret_key = load_alpaca_keys()
        self.client = TradingClient(api_key, secret_key, paper=True)

    def get_positions(self):
        return self.client.get_all_positions()

    def get_account(self):
        return self.client.get_account()

    def get_account_cash(self) -> float:
        return float(self.get_account().cash)

    def get_clock(self):
        return self.client.get_clock()

    def is_connected(self) -> bool:
        try:
            self.get_clock()
            return True
        except Exception as exc:
            log.warning("Alpaca connectivity check failed: %s", exc)
            return False

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
        try:
            order = self.client.submit_order(request)
        except Exception as exc:
            log.error("Order rejected: %s %s x %s (%s)", side.upper(), quantity, symbol, exc)
            return OrderResult(symbol, side, quantity, "rejected", None, False, error=str(exc))
        log.info("Order submitted: %s %s x %s id=%s status=%s", side.upper(), quantity, symbol, order.id, order.status)
        return OrderResult(symbol, side, quantity, _status_string(order), str(order.id), False)

    def wait_for_terminal_status(
        self,
        result: OrderResult,
        timeout_seconds: float = 30.0,
        poll_seconds: float = 2.0,
    ) -> OrderResult:
        """Poll an order until it reaches a terminal state or the timeout.

        Returns an updated OrderResult reflecting the last observed status
        (e.g. filled, partially_filled, canceled, rejected). A partially
        filled or still-open order at timeout is reported as-is so the caller
        can see the true order state instead of assuming a full fill.
        """
        if result.dry_run or result.order_id is None:
            return result
        deadline = time.monotonic() + timeout_seconds
        order = None
        while True:
            try:
                order = self.client.get_order_by_id(result.order_id)
            except Exception as exc:
                log.warning("Order status check failed for %s: %s", result.order_id, exc)
            else:
                status = _status_string(order)
                if status in TERMINAL_STATUSES:
                    break
                log.info("Order %s still open: status=%s filled=%s", result.order_id, status, order.filled_qty)
            if time.monotonic() >= deadline:
                break
            time.sleep(poll_seconds)
        if order is None:
            return result
        filled_avg_price = getattr(order, "filled_avg_price", None)
        return replace(
            result,
            status=_status_string(order),
            filled_quantity=float(order.filled_qty or 0),
            filled_avg_price=float(filled_avg_price) if filled_avg_price else None,
        )


class SimulatedBroker:
    def submit_market_order(self, symbol: str, side: str, quantity: float, dry_run: bool = True) -> OrderResult:
        return OrderResult(symbol, side, quantity, "simulated", None, True)
