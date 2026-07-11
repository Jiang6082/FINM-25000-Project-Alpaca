# FINM 25000 Project Alpaca

An Alpaca-based systematic trading system for paper trading only. The system includes a data pipeline, rule-based strategy, risk checks, execution layer, backtest mode, paper-trading mode, Streamlit dashboard, tests, and documented setup.

Repository: <https://github.com/Jiang6082/FINM-25000-Project-Alpaca>

Video walkthrough (YouTube, unlisted): <https://youtu.be/fhPcpMOMTTI>

## Team

- Charles Jiang ([@Jiang6082](https://github.com/Jiang6082))
- Peirui Liu

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
tests/                  unit tests for strategy, risk, backtest, execution
artifacts/sample/       sample backtest outputs from simulated data
```

### Module Flow

```text
 Alpaca Market Data API          (or SimulatedMarketData for no-key runs)
          |
          v
 +------------------+     OHLCV bars logged to data/live/
 |     data.py      |----------------------------------------+
 +------------------+                                        |
          |  bars                                            |
          v                                                  |
 +------------------+                                        |
 |   strategy.py    |  trend / breakout / momentum signals   |
 +------------------+                                        |
          |  ranked signals                                  |
          v                                                  v
 +------------------+     +------------------+     +--------------------+
 |     risk.py      |---->|   execution.py   |---->| Alpaca Paper API   |
 | exposure caps,   |     | submit orders,   |     | (paper=True only)  |
 | stop/take exits  |     | poll status      |     +--------------------+
 +------------------+     +------------------+
          |
          v
 +------------------+     +----------------------+
 | backtest.py      |---->| metrics.py           |
 | historical sim   |     | P&L, drawdown, hits  |
 +------------------+     +----------------------+

 engine.py + cli.py  orchestrate the modes (backtest / collect / paper)
 ui/streamlit_app.py monitors account, signals, orders and starts/stops
                     the strategy loop
```

## Strategy

The strategy is a systematic moving-average breakout model:

- Go long when the fast moving average is above the slow moving average.
- Require the close to break above the prior `breakout_window`-day high.
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
- Total-exposure budgeting: new entries are sized against
  `max_total_notional` minus the notional of positions kept open, and never
  exceed available account cash
- Paper trading client is created with `paper=True`

## Execution and Error Handling

- Market-data fetches retry up to 3 times with backoff before failing with a
  clear error message.
- Rejected or failed order submissions are captured and reported with the
  rejection reason instead of crashing the cycle.
- After each live paper submission, the order is polled until it reaches a
  terminal state, so the logs show the real outcome: `filled`,
  `partially_filled`, `canceled`, `rejected`, or still open at timeout.
- Position sizing in paper mode uses the actual Alpaca paper-account cash,
  not the configured backtest capital.
- Positions in symbols outside the configured universe are never touched, so
  a narrower demo config cannot liquidate other holdings.
- A position exited on stop-loss/take-profit is not re-entered in the same
  cycle.

## Setup

Requires Python 3.11+ (the config loader uses `tomllib`).

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Windows (PowerShell):

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
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

- system status: mode, Alpaca connected/disconnected, market open/closed
- live paper-account equity, cash, current positions, and unrealized P&L
- backtest metrics, equity curve, and drawdown
- recent signals and orders

And provides controls to:

- start/stop a recurring strategy loop (with adjustable interval)
- run a single strategy cycle on demand
- toggle dry-run (decisions only) vs. live paper submission
- adjust risk limits (max position notional, max total notional, max open
  positions) from the sidebar
- switch between backtest and paper-trading modes and between Alpaca and
  simulated data

## Tests

```bash
pip install pytest
pytest
```

Verified locally:

```text
9 passed
```

## Example Usage: Text Walkthrough

A typical end-to-end session looks like this:

1. **Install and configure.** Create a Python 3.11+ virtualenv, run
   `pip install -r requirements.txt`, copy `.env.example` to `.env`, and fill
   in your Alpaca *paper* API keys.
2. **Sanity-check with a simulated backtest** (no keys needed):

   ```bash
   python -m alpaca_trading_system.cli --config config/config.example.toml backtest --simulated --output artifacts/backtests/local
   ```

   The console prints metrics such as `total_return`, `sharpe`,
   `max_drawdown`, `num_trades`, and `hit_rate`, and writes CSVs plus equity
   and drawdown charts to the output folder.
3. **Start the dashboard** with `streamlit run alpaca_trading_system/ui/streamlit_app.py`.
   The status row shows the current mode, whether Alpaca is
   connected, and whether the market is open. With valid paper credentials
   the account panel shows equity, cash, open positions, and unrealized P&L.
4. **Run a backtest from the UI.** Keep mode on *Backtest*, click
   *Run Backtest*, and inspect the metrics table, equity curve, drawdown
   chart, and the most recent signals and orders.
5. **Dry-run the strategy.** Switch mode to *Paper trading*, keep *Dry-run*
   checked, and click *Run one cycle now*. The cycle fetches fresh Alpaca
   bars, computes signals, applies risk checks, and lists the orders it
   *would* submit — with quantities, sides, and reasons — without sending
   anything.
6. **Go live in paper mode.** During market hours, uncheck *Dry-run* and
   click *Start strategy loop*. Each cycle submits risk-checked market orders
   to the Alpaca paper account and polls each order to its final state
   (`filled`, `partially_filled`, `canceled`, or `rejected`). The account
   panel reflects the new positions; *Stop strategy loop* halts trading.
   The same cycle can be run headlessly with
   `python -m alpaca_trading_system.cli --config config/paper_demo.example.toml paper-once`.
7. **Collect data continuously** (optional) with
   `... collect-loop --interval 60`, which polls minute bars and appends
   de-duplicated rows to `data/live/bars_<date>.csv`.

## Limitations

- The backtest fills orders at the same daily close that generated the
  signal; there is no intraday fill model, transaction-cost, or slippage
  model.
- Signals are computed on daily bars; the live loop re-evaluates the same
  daily logic rather than reacting intraday.
- Market data uses the free IEX feed, which can differ from consolidated SIP
  prices.
- Orders are plain market orders; there is no limit-order or
  smart-execution logic.

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

## Video Walkthrough

Video (YouTube, unlisted): <https://youtu.be/fhPcpMOMTTI>

The video states the paper-trading disclaimer on screen at the start and end:
**"This is paper trading only. No real money is used."**

The video covers:

1. Project goal and architecture (data, strategy, risk, execution, UI).
2. The test suite passing (9 tests).
3. A backtest on real Alpaca historical data with metrics, equity curve, and
   drawdown charts.
4. The live data pipeline logging quotes to `data/live/`.
5. The Streamlit dashboard: connection status, paper-account positions and
   P&L, backtest results, and the dry-run / live strategy cycle controls.
6. Live paper-trading execution: orders submitted to the Alpaca paper
   endpoint, polled to `filled`, and verified in the Alpaca dashboard.
7. The structured event log and a reflection on limitations, improvements,
   and lessons learned.
