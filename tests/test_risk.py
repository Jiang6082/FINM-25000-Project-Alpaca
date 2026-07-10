import pandas as pd

from alpaca_trading_system.config import load_config
from alpaca_trading_system.risk import Position, target_orders


def test_risk_caps_open_positions_and_creates_exits():
    config = load_config()
    latest = pd.DataFrame(
        {
            "symbol": ["AAPL", "MSFT", "SPY", "QQQ"],
            "close": [100.0, 200.0, 400.0, 300.0],
            "score": [4.0, 3.0, 2.0, 1.0],
            "signal": [1, 1, 1, 1],
        }
    )
    orders = target_orders(latest, {}, config.risk.initial_capital, config.risk)
    buys = [order for order in orders if order["side"] == "buy"]
    assert len(buys) <= config.risk.max_open_positions
    assert all(order["quantity"] > 0 for order in buys)

    positions = {"AAPL": Position("AAPL", 10, 100.0, 94.0)}
    exits = target_orders(latest, positions, config.risk.initial_capital, config.risk)
    assert any(order["side"] == "sell" and order["symbol"] == "AAPL" for order in exits)


def test_total_exposure_stays_within_cap_with_existing_positions():
    config = load_config()
    latest = pd.DataFrame(
        {
            "symbol": ["AAPL", "MSFT", "SPY"],
            "close": [100.0, 200.0, 400.0],
            "score": [3.0, 2.0, 1.0],
            "signal": [1, 1, 1],
        }
    )
    held_notional = 40_000.0
    positions = {
        "AAPL": Position("AAPL", 200, 100.0, 100.0),
        "MSFT": Position("MSFT", 100, 200.0, 200.0),
    }
    orders = target_orders(latest, positions, 60_000.0, config.risk)
    assert not any(order["side"] == "sell" for order in orders)
    new_notional = sum(order["quantity"] * 400.0 for order in orders if order["side"] == "buy")
    assert new_notional <= config.risk.max_total_notional - held_notional


def test_stop_loss_exit_is_not_reentered_in_same_cycle():
    config = load_config()
    latest = pd.DataFrame({"symbol": ["AAPL"], "close": [94.0], "score": [5.0], "signal": [1]})
    positions = {"AAPL": Position("AAPL", 10, 100.0, 94.0)}
    orders = target_orders(latest, positions, 100_000.0, config.risk)
    assert [order["side"] for order in orders if order["symbol"] == "AAPL"] == ["sell"]


def test_buys_never_exceed_available_cash_without_leverage():
    config = load_config()
    latest = pd.DataFrame(
        {
            "symbol": ["AAPL", "MSFT"],
            "close": [100.0, 200.0],
            "score": [2.0, 1.0],
            "signal": [1, 1],
        }
    )
    cash = 1_000.0
    prices = {"AAPL": 100.0, "MSFT": 200.0}
    orders = target_orders(latest, {}, cash, config.risk)
    spend = sum(order["quantity"] * prices[order["symbol"]] for order in orders)
    assert spend <= cash
