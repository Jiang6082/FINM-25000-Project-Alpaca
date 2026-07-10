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
