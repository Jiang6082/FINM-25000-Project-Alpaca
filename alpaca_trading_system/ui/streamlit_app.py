from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from alpaca_trading_system.config import load_config
from alpaca_trading_system.engine import paper_once, run_backtest_workflow


st.set_page_config(page_title="Project Alpaca", layout="wide")
st.title("Project Alpaca: Paper Trading System")

config_path = st.sidebar.text_input("Config path", "config/config.example.toml")
config = load_config(config_path)
mode = st.sidebar.radio("Mode", ["Backtest", "Paper dry-run"], index=0)
simulated = st.sidebar.checkbox("Use simulated data", value=True)

st.sidebar.write("Paper trading only:", config.system.paper_trading_only)
st.sidebar.write("Tickers:", ", ".join(config.tickers))

st.subheader("System Status")
status_cols = st.columns(4)
status_cols[0].metric("Mode", mode)
status_cols[1].metric("Universe", len(config.tickers))
status_cols[2].metric("Max Positions", config.risk.max_open_positions)
status_cols[3].metric("Max Total Notional", f"${config.risk.max_total_notional:,.0f}")

if mode == "Backtest":
    output_dir = Path("artifacts/backtests/ui")
    if st.button("Run Backtest"):
        output = run_backtest_workflow(config, simulated=simulated, output_dir=output_dir)
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
    st.warning("Dry-run is recommended until you are ready to demo in Alpaca paper trading.")
    if st.button("Run Paper Dry-Run"):
        results = paper_once(config, dry_run=True, simulated=simulated)
        st.subheader("Order Decisions")
        st.dataframe(results if len(results) else pd.DataFrame({"message": ["No orders generated."]}))
