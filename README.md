# FINM 25000 Project Alpaca

An Alpaca-based systematic trading system for paper trading only. The system includes a data pipeline, rule-based strategy, risk checks, execution layer, backtest mode, paper-trading mode, Streamlit dashboard, tests, and documented setup.

Repository: <https://github.com/Jiang6082/FINM-25000-Project-Alpaca>

## Safety

This project is built for **Alpaca paper trading only**. It does not require or use real-money trading. API keys are loaded from `.env`, which is excluded from GitHub.

## Architecture

```text
config/                 parameters, ticker universe, risk limits
alpaca_trading_system/
  config.py             TOML config loading
  data.py               Alpaca and simulated data providers
  strategy.py           systematic signal generation
  risk.py               exposure, position, stop-loss/take-profit checks
  execution.py          paper-only Alpaca order routing
  backtest.py           historical long-only simulation
  metrics.py            P&L, drawdown, trades, hit rate
  engine.py             orchestration for backtest and paper runs
  cli.py                command-line entry points
  ui/streamlit_app.py   monitoring and control dashboard
tests/                  unit tests for strategy, risk, backtest
artifacts/sample/       sample backtest outputs from simulated data
```

## Strategy

The strategy is a systematic moving-average breakout model:

- Go long when the fast moving average is above the slow moving average.
- Require positive recent momentum versus the breakout lookback.
- Rank candidates by momentum divided by realized volatility.
- Hold at most `max_symbols` names.
- Stay flat when trend/breakout conditions are not met.

The market behavior assumption is that large liquid equities and ETFs can show short-term continuation after trend confirmation. The volatility adjustment avoids concentrating only in the most explosive names.

## Risk Controls

- Long-only
- No leverage
- No short selling
- Maximum notional per asset
- Maximum total notional exposure
- Maximum open positions
- Stop-loss and take-profit exits
- Paper trading client is created with `paper=True`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

For Alpaca paper mode, fill `.env` with paper API credentials:

```bash
ALPACA_API_KEY=...
ALPACA_SECRET_KEY=...
```

Never commit `.env`.

## Run Backtest Mode

Backtest mode can run without Alpaca credentials using simulated market data:

```bash
python -m alpaca_trading_system.cli --config config/config.example.toml backtest --simulated --output artifacts/backtests/local
```

It writes:

- `metrics.csv`
- `equity_curve.csv`
- `orders.csv`
- `signals.csv`
- `equity_curve.png`
- `drawdown.png`

## Run Paper Trading Mode

Use `--dry-run` first:

```bash
python -m alpaca_trading_system.cli --config config/config.example.toml paper-once --dry-run
```

Then, during market hours and only after confirming the account is paper trading:

```bash
python -m alpaca_trading_system.cli --config config/config.example.toml paper-once
```

The paper run fetches recent Alpaca bars, generates signals, checks risk limits, and submits market orders through Alpaca's paper endpoint.

For a small paper-demo order, use the demo config. It limits the universe to
`AAPL`, uses shorter signal windows, and caps notional exposure at `$500`:

```bash
python -m alpaca_trading_system.cli --config config/paper_demo.example.toml paper-once
```

## Run Data Collection

```bash
python -m alpaca_trading_system.cli --config config/config.example.toml collect-once
```

This logs current bar snapshots into `data/live/`.

To run a continuous polling loop:

```bash
python -m alpaca_trading_system.cli --config config/config.example.toml collect-loop --interval 60
```

Use `Ctrl+C` to stop it.

## Run UI

```bash
streamlit run alpaca_trading_system/ui/streamlit_app.py
```

The dashboard shows:

- system status and selected mode
- current strategy configuration
- backtest metrics
- equity curve and drawdown
- recent signals and orders
- paper-trading dry-run controls

## Tests

```bash
pip install pytest
pytest
```

Verified locally:

```text
3 passed
```

## Sample Outputs

`artifacts/sample/` contains a sample simulated backtest so the repo has visible output artifacts even before live Alpaca credentials are added.

## Alpaca Paper Run Evidence

After adding local paper credentials, the Alpaca-backed paths were run on
July 10, 2026:

- `artifacts/alpaca_run/latest_bars_snapshot.csv`: latest Alpaca market-data snapshot for AAPL, MSFT, NVDA, QQQ, and SPY
- `artifacts/alpaca_run/metrics.csv`: Alpaca-data backtest metrics
- `artifacts/alpaca_run/equity_curve.png`: Alpaca-data equity curve
- `artifacts/alpaca_run/drawdown.png`: Alpaca-data drawdown chart
- `artifacts/alpaca_run/orders.csv`: backtest order log
- `artifacts/alpaca_run/trades.csv`: backtest trade/P&L log
- `artifacts/alpaca_run/paper_order_evidence.md`: non-sensitive paper order status note
- `artifacts/alpaca_run/paper_order_status.csv`: non-sensitive paper order status table
- `artifacts/alpaca_run/paper_positions_snapshot.csv`: non-sensitive paper position snapshot

The paper order was submitted through an Alpaca `TradingClient` constructed
with `paper=True`. The order filled in the Alpaca paper account during regular
market hours.

## What Still Requires Human Work

- Save dashboard screenshots showing the paper account and filled order/trade state.
- Record the required 10-15 minute video walkthrough.
- In the video, say clearly: **"This is paper trading only. No real money is used."**
- Add the final video link here before Canvas submission:

```text
VIDEO LINK: TODO
```

## Video Outline

1. Project goal and paper-trading safety statement.
2. Architecture: data, strategy, risk, execution, UI.
3. Run the Streamlit dashboard.
4. Show backtest metrics, equity curve, drawdown, signals, and orders.
5. Run paper-trading demo in Alpaca paper mode.
6. Show Alpaca dashboard order/trade evidence.
7. Discuss limitations: simulated sample data, simple rule-based strategy, no transaction-cost model beyond basic assumptions, and need for robust production monitoring.
