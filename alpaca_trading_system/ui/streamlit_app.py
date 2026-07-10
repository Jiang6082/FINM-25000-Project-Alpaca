from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import time

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from alpaca_trading_system.config import load_config
from alpaca_trading_system.data import MissingAlpacaCredentials
from alpaca_trading_system.engine import paper_once, run_backtest_workflow
from alpaca_trading_system.execution import PaperBroker


st.set_page_config(page_title="Project Alpaca", layout="wide")
st.title("Project Alpaca: Paper Trading System")


@st.cache_resource
def get_broker() -> PaperBroker | None:
    try:
        return PaperBroker()
    except MissingAlpacaCredentials:
        return None


@st.cache_data(ttl=30)
def connection_status() -> dict:
    broker = get_broker()
    if broker is None:
        return {"connected": False, "market_open": None, "detail": "No Alpaca credentials found in .env."}
    try:
        clock = broker.get_clock()
        return {"connected": True, "market_open": bool(clock.is_open), "detail": "Alpaca paper endpoint reachable."}
    except Exception as exc:
        return {"connected": False, "market_open": None, "detail": f"Alpaca connection failed: {exc}"}


# --- Sidebar: mode, data source, and adjustable risk limits ---
config_path = st.sidebar.text_input("Config path", "config/config.example.toml")
config = load_config(config_path)
mode = st.sidebar.radio("Mode", ["Backtest", "Paper trading"], index=0)
simulated = st.sidebar.checkbox("Use simulated data", value=True)

st.sidebar.subheader("Risk Limits")
max_position_notional = st.sidebar.number_input(
    "Max position notional ($)", min_value=100.0, value=float(config.risk.max_position_notional), step=500.0
)
max_total_notional = st.sidebar.number_input(
    "Max total notional ($)", min_value=100.0, value=float(config.risk.max_total_notional), step=1000.0
)
max_open_positions = st.sidebar.number_input(
    "Max open positions", min_value=1, value=config.risk.max_open_positions, step=1
)
config = replace(
    config,
    risk=replace(
        config.risk,
        max_position_notional=float(max_position_notional),
        max_total_notional=float(max_total_notional),
        max_open_positions=int(max_open_positions),
    ),
)

st.sidebar.write("Paper trading only:", config.system.paper_trading_only)
st.sidebar.write("Tickers:", ", ".join(config.tickers))

# --- System status ---
status = connection_status()
st.subheader("System Status")
status_cols = st.columns(5)
status_cols[0].metric("Mode", mode)
status_cols[1].metric("Alpaca", "Connected" if status["connected"] else "Disconnected")
market_label = "n/a" if status["market_open"] is None else ("Open" if status["market_open"] else "Closed")
status_cols[2].metric("Market", market_label)
status_cols[3].metric("Universe", len(config.tickers))
status_cols[4].metric("Max Total Notional", f"${config.risk.max_total_notional:,.0f}")
st.caption(status["detail"])

# --- Paper account: positions and P&L ---
st.subheader("Paper Account: Positions and P&L")
broker = get_broker()
if broker is None or not status["connected"]:
    st.info("Add Alpaca paper credentials to .env to see live account positions and P&L.")
else:
    try:
        account = broker.get_account()
        positions = broker.get_positions()
        unrealized = sum(float(p.unrealized_pl or 0) for p in positions)
        account_cols = st.columns(3)
        account_cols[0].metric("Equity", f"${float(account.equity):,.2f}")
        account_cols[1].metric("Cash", f"${float(account.cash):,.2f}")
        account_cols[2].metric("Unrealized P&L", f"${unrealized:,.2f}")
        if positions:
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "symbol": p.symbol,
                            "qty": float(p.qty),
                            "avg_entry": float(p.avg_entry_price),
                            "current": float(p.current_price or 0),
                            "market_value": float(p.market_value or 0),
                            "unrealized_pl": float(p.unrealized_pl or 0),
                        }
                        for p in positions
                    ]
                )
            )
        else:
            st.write("No open positions.")
    except Exception as exc:
        st.error(f"Failed to load account data: {exc}")

# --- Mode panels ---
if mode == "Backtest":
    output_dir = Path("artifacts/backtests/ui")
    if st.button("Run Backtest"):
        try:
            output = run_backtest_workflow(config, simulated=simulated, output_dir=output_dir)
        except Exception as exc:
            st.error(f"Backtest failed: {exc}")
        else:
            st.success(f"Backtest complete. Artifacts saved to {output_dir}.")
            metrics = pd.DataFrame([output.metrics]).T.rename(columns={0: "value"})
            st.subheader("Performance Metrics")
            st.dataframe(metrics)
            st.subheader("Equity Curve")
            st.line_chart(output.equity)
            st.subheader("Drawdown")
            st.line_chart(output.equity / output.equity.cummax() - 1)
            st.subheader("Recent Signals")
            st.dataframe(output.signals.tail(30))
            st.subheader("Orders")
            st.dataframe(output.orders.tail(30))
else:
    dry_run = st.checkbox("Dry-run (log order decisions without submitting)", value=True)
    if not dry_run:
        st.warning("Dry-run disabled: orders WILL be submitted to the Alpaca paper account.")
    interval = st.number_input("Loop interval (seconds)", min_value=10, value=60, step=10)

    if "strategy_running" not in st.session_state:
        st.session_state.strategy_running = False

    start_col, stop_col = st.columns(2)
    if start_col.button("Start strategy loop", disabled=st.session_state.strategy_running):
        st.session_state.strategy_running = True
    if stop_col.button("Stop strategy loop", disabled=not st.session_state.strategy_running):
        st.session_state.strategy_running = False

    st.write("Strategy loop:", "RUNNING" if st.session_state.strategy_running else "stopped")
    run_once = st.button("Run one cycle now")

    if run_once or st.session_state.strategy_running:
        try:
            results = paper_once(config, dry_run=dry_run, simulated=simulated)
        except Exception as exc:
            st.error(f"Strategy cycle failed: {exc}")
            st.session_state.strategy_running = False
        else:
            st.subheader(f"Cycle Result ({pd.Timestamp.now().strftime('%H:%M:%S')})")
            if len(results):
                st.dataframe(results)
            else:
                st.write("No orders generated this cycle.")
        if st.session_state.strategy_running:
            time.sleep(int(interval))
            st.rerun()
