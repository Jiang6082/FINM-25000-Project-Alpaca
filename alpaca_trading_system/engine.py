from __future__ import annotations

import logging
from pathlib import Path
import time

import pandas as pd

from alpaca_trading_system.backtest import run_backtest, save_backtest_output
from alpaca_trading_system.config import AppConfig
from alpaca_trading_system.data import AlpacaMarketData, SimulatedMarketData, append_bar_log
from alpaca_trading_system.execution import PaperBroker, SimulatedBroker
from alpaca_trading_system.risk import Position, target_orders
from alpaca_trading_system.strategy import generate_signals, latest_signals


log = logging.getLogger(__name__)


def get_data_provider(simulated: bool):
    return SimulatedMarketData() if simulated else AlpacaMarketData()


def run_backtest_workflow(config: AppConfig, simulated: bool, output_dir: Path):
    provider = get_data_provider(simulated)
    bars = provider.fetch_bars(config.tickers, lookback_days=260)
    output = run_backtest(bars, config)
    save_backtest_output(output, output_dir)
    return output


def collect_once(config: AppConfig, simulated: bool = False) -> Path:
    """Fetch recent quotes and append them to the daily data log.

    Uses minute bars so repeated polling during market hours captures fresh
    prices; falls back to daily bars when no minute data is available (e.g.
    outside market hours).
    """
    provider = get_data_provider(simulated)
    bars = provider.fetch_bars(config.tickers, lookback_days=1, timeframe="minute")
    if bars.empty:
        log.info("No minute bars available; falling back to daily bars.")
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
    """Run one strategy cycle: fetch data, generate signals, submit orders."""
    provider = get_data_provider(simulated)
    bars = provider.fetch_bars(config.tickers, lookback_days=90)
    append_bar_log(bars.tail(len(config.tickers)), config.system.data_dir)
    signal_snapshot = latest_signals(generate_signals(bars, config.strategy))
    log.info(
        "Signals generated: %s active out of %s symbols",
        int(signal_snapshot["signal"].sum()),
        len(signal_snapshot),
    )

    if simulated:
        broker = SimulatedBroker()
        positions: dict[str, Position] = {}
        cash = config.risk.initial_capital
    else:
        broker = PaperBroker()
        positions = _positions_from_broker(broker, signal_snapshot, config.tickers)
        cash = broker.get_account_cash()
        log.info("Paper account cash: %.2f, tracked positions: %s", cash, sorted(positions))

    orders = target_orders(signal_snapshot, positions, cash, config.risk)
    results = []
    for order in orders:
        result = broker.submit_market_order(order["symbol"], order["side"], order["quantity"], dry_run=dry_run)
        if not dry_run and isinstance(broker, PaperBroker) and result.order_id:
            result = broker.wait_for_terminal_status(result)
        log.info(
            "Order %s %s x %s -> status=%s filled=%s",
            order["side"].upper(),
            order["symbol"],
            order["quantity"],
            result.status,
            result.filled_quantity,
        )
        results.append(result.__dict__ | {"reason": order["reason"]})
    return pd.DataFrame(results)


def _positions_from_broker(
    broker: PaperBroker,
    signal_snapshot: pd.DataFrame,
    universe: list[str],
) -> dict[str, Position]:
    """Read paper-account positions, restricted to the configured universe.

    Positions in symbols outside the universe are left untouched so running
    with a narrower config (e.g. the paper demo) never liquidates holdings
    the strategy does not manage.
    """
    latest_prices = signal_snapshot.set_index("symbol")["close"].to_dict()
    tracked = set(universe)
    positions: dict[str, Position] = {}
    for item in broker.get_positions():
        symbol = item.symbol
        if symbol not in tracked:
            log.info("Ignoring position in %s: not in configured universe.", symbol)
            continue
        market_price = float(getattr(item, "current_price", 0) or latest_prices.get(symbol, 0))
        positions[symbol] = Position(
            symbol=symbol,
            quantity=float(item.qty),
            avg_entry_price=float(item.avg_entry_price),
            market_price=market_price,
        )
    return positions
