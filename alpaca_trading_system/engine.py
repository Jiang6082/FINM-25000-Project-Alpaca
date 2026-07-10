from __future__ import annotations

from pathlib import Path
import time

import pandas as pd

from alpaca_trading_system.backtest import run_backtest, save_backtest_output
from alpaca_trading_system.config import AppConfig
from alpaca_trading_system.data import AlpacaMarketData, SimulatedMarketData, append_bar_log
from alpaca_trading_system.execution import PaperBroker, SimulatedBroker
from alpaca_trading_system.risk import Position, target_orders
from alpaca_trading_system.strategy import generate_signals, latest_signals


def get_data_provider(simulated: bool):
    return SimulatedMarketData() if simulated else AlpacaMarketData()


def run_backtest_workflow(config: AppConfig, simulated: bool, output_dir: Path):
    provider = get_data_provider(simulated)
    bars = provider.fetch_bars(config.tickers, lookback_days=260)
    output = run_backtest(bars, config)
    save_backtest_output(output, output_dir)
    return output


def collect_once(config: AppConfig, simulated: bool = False) -> Path:
    provider = get_data_provider(simulated)
    bars = provider.fetch_bars(config.tickers, lookback_days=5)
    return append_bar_log(bars, config.system.data_dir)


def collect_loop(config: AppConfig, simulated: bool = False, interval_seconds: int = 60, iterations: int | None = None):
    count = 0
    while True:
        yield collect_once(config, simulated=simulated)
        count += 1
        if iterations is not None and count >= iterations:
            break
        time.sleep(interval_seconds)


def paper_once(config: AppConfig, dry_run: bool = True, simulated: bool = False) -> pd.DataFrame:
    provider = get_data_provider(simulated)
    bars = provider.fetch_bars(config.tickers, lookback_days=90)
    append_bar_log(bars.tail(len(config.tickers)), config.system.data_dir)
    signal_snapshot = latest_signals(generate_signals(bars, config.strategy))
    broker = SimulatedBroker() if simulated else PaperBroker()
    positions = {} if simulated else _positions_from_broker(broker, signal_snapshot)
    orders = target_orders(signal_snapshot, positions, config.risk.initial_capital, config.risk)
    results = []
    for order in orders:
        result = broker.submit_market_order(order["symbol"], order["side"], order["quantity"], dry_run=dry_run)
        results.append(result.__dict__ | {"reason": order["reason"]})
    return pd.DataFrame(results)


def _positions_from_broker(broker: PaperBroker, signal_snapshot: pd.DataFrame) -> dict[str, Position]:
    latest_prices = signal_snapshot.set_index("symbol")["close"].to_dict()
    positions: dict[str, Position] = {}
    for item in broker.get_positions():
        symbol = item.symbol
        market_price = float(getattr(item, "current_price", 0) or latest_prices.get(symbol, 0))
        positions[symbol] = Position(
            symbol=symbol,
            quantity=float(item.qty),
            avg_entry_price=float(item.avg_entry_price),
            market_price=market_price,
        )
    return positions
