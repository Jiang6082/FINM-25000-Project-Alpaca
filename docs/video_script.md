# Project Alpaca Video Script

Target length: 10-15 minutes.

Recording style: record in short chunks. Each chunk below has a screen action, optional terminal commands, and voiceover text you can read directly.

Important line to say clearly at least once:

```text
This is paper trading only. No real money is used.
```

## Chunk 1: Opening And Safety Statement

Screen action:

- Show the GitHub repository home page.
- Show the README title and safety section.

Voiceover:

> Hi, this is our FINM 25000 Project Alpaca submission. We built an end-to-end systematic trading system using Alpaca for market data and paper-trading order routing. The system includes a data pipeline, a rule-based strategy, a risk layer, a backtest engine, a paper execution layer, and a Streamlit dashboard. This is paper trading only. No real money is used.

## Chunk 2: Repository Structure

Screen action:

- Scroll to the README architecture section.
- Open the `alpaca_trading_system/` folder in GitHub or your editor.

Voiceover:

> The project is organized into separate modules. `config.py` loads TOML configuration files. `data.py` handles Alpaca and simulated market data. `strategy.py` creates systematic trading signals. `risk.py` checks position limits, exposure limits, stop-loss, and take-profit rules. `execution.py` submits orders through Alpaca's paper endpoint. `backtest.py` runs historical simulations, and `ui/streamlit_app.py` provides the dashboard.

## Chunk 3: Setup And Configuration

Screen action:

- Show `config/config.example.toml`.
- Show `.env.example`.
- Do not show the real `.env` contents.

Voiceover:

> The system is configured through TOML files and environment variables. The ticker universe, strategy parameters, and risk limits are all in `config/config.example.toml`. Alpaca credentials are stored locally in `.env`, which is excluded from GitHub by `.gitignore`. We only commit `.env.example`, which has dummy placeholders.

Optional terminal commands to show:

```bash
cd /Users/charles/Documents/Playground/FINM-25000-Project-Alpaca
source .venv/bin/activate
git status --short --ignored .env
```

Voiceover after command:

> The real `.env` file is ignored, so API keys are not committed to GitHub.

## Chunk 4: Strategy Logic

Screen action:

- Open `alpaca_trading_system/strategy.py`.
- Highlight `compute_indicators` and `generate_signals`.

Voiceover:

> The strategy is a moving-average breakout system. It goes long only when the fast moving average is above the slow moving average, the latest price is breaking above a recent high, and momentum is positive. When multiple assets qualify, the system ranks them by momentum divided by realized volatility. This makes the strategy systematic and repeatable, with no discretionary clicking.

## Chunk 5: Risk Management

Screen action:

- Open `alpaca_trading_system/risk.py`.
- Show `config/config.example.toml` risk settings.

Voiceover:

> The risk layer enforces long-only trading, no leverage, no short selling, maximum notional per asset, maximum total notional exposure, and a maximum number of open positions. It also creates exits for stop-loss and take-profit conditions. The trading engine does not send raw strategy signals directly to Alpaca; signals first pass through this risk layer.

## Chunk 6: Data Pipeline

Screen action:

- Open `alpaca_trading_system/data.py`.
- Then show `artifacts/alpaca_run/latest_bars_snapshot.csv`.

Terminal command:

```bash
python -m alpaca_trading_system.cli --config config/config.example.toml collect-once
```

Voiceover:

> The data pipeline fetches recent OHLCV bars from Alpaca for our configured universe: AAPL, MSFT, SPY, QQQ, and NVDA. The system can also run a continuous polling loop for live monitoring. Incoming bars are stored as structured CSV data with timestamps, symbols, prices, and volumes.

Optional continuous-loop command to mention, but do not leave running during the video:

```bash
python -m alpaca_trading_system.cli --config config/config.example.toml collect-loop --interval 60
```

## Chunk 7: Backtest

Screen action:

- Run the backtest command.
- Show `artifacts/alpaca_run/metrics.csv`.
- Show `artifacts/alpaca_run/equity_curve.png`.
- Show `artifacts/alpaca_run/drawdown.png`.

Terminal command:

```bash
python -m alpaca_trading_system.cli --config config/config.example.toml backtest --output artifacts/alpaca_run
```

Voiceover:

> This command runs the strategy on Alpaca historical data and saves the backtest artifacts. The backtest tracks equity, orders, trades, signals, drawdown, and performance metrics. The key metrics include total return, CAGR, volatility, Sharpe ratio, Sortino ratio, max drawdown, number of trades, and hit rate.

Voiceover for the specific run:

> In our saved Alpaca run, the strategy produced 49 trades. The total return was about negative 0.65 percent, the max drawdown was about negative 1.57 percent, and the hit rate was about 34.7 percent. This is not presented as a production-ready alpha model; it is a working systematic trading architecture with measurable outputs.

## Chunk 8: Tests

Screen action:

- Run tests in terminal.

Terminal command:

```bash
pytest
```

Voiceover:

> We added tests for the strategy, risk logic, and backtest outputs. The tests verify that signals are long or flat, risk limits are applied, and the backtest produces usable metrics and artifacts.

Expected output:

```text
3 passed
```

## Chunk 9: Streamlit Dashboard

Screen action:

- Start Streamlit.
- Open `http://localhost:8501`.
- Show the dashboard status, configuration, metrics, equity curve, drawdown, signals, and orders.

Terminal command:

```bash
streamlit run alpaca_trading_system/ui/streamlit_app.py
```

Voiceover:

> The Streamlit UI provides a simple way to monitor and control the system. It shows system status, the selected ticker universe, maximum position limits, backtest metrics, equity curve, drawdown, recent signals, and recent orders. The dashboard can run in simulated mode for safe demonstrations and can also use the configured paper-trading workflow.

## Chunk 10: Paper Trading Demo

Screen action:

- Show `config/paper_demo.example.toml`.
- Show the paper demo command.
- Show `artifacts/alpaca_run/paper_order_evidence.md`.
- Show `artifacts/alpaca_run/paper_order_status.csv`.
- Show the Alpaca paper dashboard with the filled AAPL order.

Terminal command for dry run:

```bash
python -m alpaca_trading_system.cli --config config/paper_demo.example.toml paper-once --dry-run
```

Terminal command for paper order:

```bash
python -m alpaca_trading_system.cli --config config/paper_demo.example.toml paper-once
```

Voiceover:

> For the paper demo, we used a separate demo config that limits the universe to AAPL and caps notional exposure at 500 dollars. We first ran a dry run, then submitted an order through Alpaca paper trading. The execution layer constructs the Alpaca `TradingClient` with `paper=True`, so the order is routed to the paper account only.

Voiceover for the saved order evidence:

> The saved evidence shows that the system submitted a market buy order for 1 share of AAPL. The order status is filled, with filled quantity 1 and filled average price 314.61. The position snapshot also shows an AAPL paper position. Again, this is paper trading only. No real money is used.

## Chunk 11: Alpaca Dashboard Evidence

Screen action:

- Show the Alpaca paper dashboard.
- Show account mode is paper.
- Show the filled order or current AAPL position.

Voiceover:

> Here we are in the Alpaca paper trading dashboard. This confirms the order and position were created in the paper account. The dashboard evidence is important because the assignment requires showing the system running in Alpaca's paper environment, not just a backtest.

## Chunk 12: Limitations And Improvements

Screen action:

- Show README limitation/video outline section or keep dashboard visible.

Voiceover:

> There are several limitations. The strategy is intentionally simple, using moving averages and breakout rules rather than a complex production model. The backtest does not fully model slippage, partial fills, or transaction costs. The UI is a lightweight monitoring dashboard, not a production operations console. Future improvements would include better fill simulation, richer monitoring, portfolio-level optimization, alerts, more robust streaming data, and expanded testing around live order states.

## Chunk 13: Closing

Screen action:

- Return to GitHub README.
- Show repo URL.

Voiceover:

> In summary, this project implements a complete Alpaca-based systematic trading system with data collection, signal generation, risk management, backtesting, paper execution, UI monitoring, tests, and documented evidence from an Alpaca paper order. The GitHub repository contains the full codebase, configuration templates, sample artifacts, Alpaca run artifacts, and instructions for reproducing the workflow.

## Quick Copy-Paste Command Block

Use this block during recording if you want the cleanest terminal sequence:

```bash
cd /Users/charles/Documents/Playground/FINM-25000-Project-Alpaca
source .venv/bin/activate
pytest
python -m alpaca_trading_system.cli --config config/config.example.toml collect-once
python -m alpaca_trading_system.cli --config config/config.example.toml backtest --output artifacts/alpaca_run
python -m alpaca_trading_system.cli --config config/paper_demo.example.toml paper-once --dry-run
streamlit run alpaca_trading_system/ui/streamlit_app.py
```

Only run the real paper-order command if you intentionally want to submit another paper order:

```bash
python -m alpaca_trading_system.cli --config config/paper_demo.example.toml paper-once
```

## Team Contribution Line

Use or adapt this in the video:

> Charles focused on the system implementation, Alpaca integration, backtesting, and paper-order evidence. Patrick focused on final presentation, dashboard/order screenshots, video assembly, and README submission polish. Both members contributed to the design and explanation of the final trading system.
