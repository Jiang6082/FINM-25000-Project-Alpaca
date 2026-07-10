from alpaca_trading_system.execution import OrderResult, PaperBroker


class _RejectingClient:
    def submit_order(self, request):
        raise RuntimeError("insufficient buying power")


class _FilledOrder:
    status = "filled"
    filled_qty = "1"
    filled_avg_price = "100.5"


class _PollClient:
    def get_order_by_id(self, order_id):
        return _FilledOrder()


def _broker_with(client) -> PaperBroker:
    broker = PaperBroker.__new__(PaperBroker)
    broker.client = client
    return broker


def test_rejected_order_is_captured_not_raised():
    broker = _broker_with(_RejectingClient())
    result = broker.submit_market_order("AAPL", "buy", 1, dry_run=False)
    assert result.status == "rejected"
    assert result.order_id is None
    assert "buying power" in result.error


def test_dry_run_order_never_touches_the_client():
    broker = _broker_with(None)
    result = broker.submit_market_order("AAPL", "buy", 1, dry_run=True)
    assert result.status == "dry_run"
    assert result.dry_run is True


def test_wait_for_terminal_status_reports_fill_details():
    broker = _broker_with(_PollClient())
    submitted = OrderResult("AAPL", "buy", 1, "accepted", "order-1", False)
    result = broker.wait_for_terminal_status(submitted, timeout_seconds=1, poll_seconds=0)
    assert result.status == "filled"
    assert result.filled_quantity == 1.0
    assert result.filled_avg_price == 100.5
