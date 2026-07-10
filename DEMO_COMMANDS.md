# L4 Demo PowerShell Command List

## PART 0 - Before recording (anytime)

step 1. Go to the project folder (run this first in every new terminal)

```powershell
cd "c:\Users\patri\Desktop\2026暑假学习\qfinance\algorithmic-trading_uchicago\L4\FINM-25000-Project-Alpaca"
```

step 2. Allow scripts for this session

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

step 3. Activate the virtual environment (prompt shows `(.venv)`)

```powershell
.\.venv\Scripts\Activate.ps1
```

step 4. Self-check: tests pass (expect `9 passed`) and Alpaca paper endpoint reachable

```powershell
python -m pytest -q
python -c "from alpaca_trading_system.execution import PaperBroker; b = PaperBroker(); c = b.get_clock(); a = b.get_account(); print('Connected to Alpaca PAPER. Market open:', c.is_open, '| Equity:', a.equity)"
```

step 4b. Clean old test logs so the recording shows fresh data only (safe: all regenerated)

```powershell
Remove-Item data\live\*.csv, logs\system.log -ErrorAction SilentlyContinue
```

## PART 1 - While recording (market hours only! Start Win+G, then begin at step 5)

step 5. Opening disclaimer (keep on screen ~5 seconds)

```powershell
Write-Host "`n   THIS IS PAPER TRADING ONLY - NO REAL MONEY IS USED.   `n" -BackgroundColor DarkRed -ForegroundColor White
```

step 6. Project introduction (hold ~15 seconds)

```powershell
Write-Host "`nFINM 25000 GROUP PROJECT - ALPACA SYSTEMATIC TRADING SYSTEM`n`nAn end-to-end system: live Alpaca data pipeline, rule-based strategy,`nrisk checks, paper-only execution, a backtester, and a Streamlit dashboard.`nEvery order goes to the Alpaca PAPER endpoint (TradingClient paper=True).`n" -ForegroundColor Cyan
```

step 7. Architecture overview (hold ~30 seconds)

```powershell
Write-Host "`nARCHITECTURE (one module per responsibility)`n`n  Alpaca API -> data.py      fetch + log OHLCV bars (retry with backoff)`n             -> strategy.py  MA breakout + momentum/volatility ranking`n             -> risk.py      exposure caps, stop-loss / take-profit exits`n             -> execution.py submit paper orders, poll to final state`n`n  backtest.py + metrics.py   historical simulation, P&L, drawdown, hit rate`n  engine.py  + cli.py        orchestrate backtest / collect / paper modes`n  ui/streamlit_app.py        dashboard: monitor account, start/stop strategy`n" -ForegroundColor Cyan
```

step 8. Show the test suite passing (unit tests for strategy, risk, backtest, execution)

```powershell
python -m pytest -q
```

step 9. Strategy explanation (hold ~30 seconds)

```powershell
Write-Host "`nSTRATEGY: moving-average breakout, long/flat, fully systematic`n`n  ENTER LONG when: fast SMA(10) > slow SMA(30)   (trend filter)`n             AND: close > prior 20-day high      (breakout confirm)`n  RANK candidates by momentum / realized volatility, hold top 3`n  EXIT on: rank drop-out, stop-loss -5%, or take-profit +10%`n`nIntuition: liquid large caps show short-term continuation after a`nconfirmed trend; volatility scaling avoids the most explosive names.`n" -ForegroundColor Cyan
```

step 10. Run a backtest on REAL Alpaca historical data (prints metrics table)

```powershell
python -m alpaca_trading_system.cli --config config/config.example.toml backtest --output artifacts\backtests\demo
```

step 11. Show the 2 backtest figures (hold each ~15 seconds)

```powershell
Invoke-Item artifacts\backtests\demo\equity_curve.png
Invoke-Item artifacts\backtests\demo\drawdown.png
```

step 12. Data pipeline: explain, collect live quotes, show the log file

```powershell
Write-Host "`nDATA PIPELINE`n  Polls Alpaca bars for AAPL MSFT SPY QQQ NVDA (free IEX feed)`n  Appends de-duplicated rows to data\live\bars_<date>.csv`n  collect-loop repeats this every N seconds; fetches retry 3x on errors`n" -ForegroundColor Cyan
python -m alpaca_trading_system.cli --config config/config.example.toml collect-once
Get-Content (Get-ChildItem data\live\*.csv | Sort-Object LastWriteTime | Select-Object -Last 1) -TotalCount 6
```

step 13. UI checklist (hold ~20 seconds), then launch the dashboard in a new window

```powershell
Write-Host "`nNEXT: STREAMLIT DASHBOARD - what to watch`n  1  Status row: mode, Alpaca CONNECTED, market OPEN`n  2  Paper account: equity, cash, positions, unrealized P&L`n  3  Backtest mode: metrics, equity curve, drawdown, signals, orders`n  4  Paper trading mode: dry-run first, then real paper orders`n  5  Sidebar: adjustable risk limits + Start/Stop strategy loop`n" -ForegroundColor Cyan
Start-Process .\.venv\Scripts\streamlit.exe -ArgumentList 'run','alpaca_trading_system\ui\streamlit_app.py'
```

--> Switch to the browser (http://localhost:8501). Walk through: status row, account
panel, sidebar risk limits. Run a backtest in Backtest mode. Then switch mode to
"Paper trading", keep Dry-run CHECKED, click "Run one cycle now" and show the table.

step 14. Risk controls explanation (back in terminal, hold ~25 seconds)

```powershell
Write-Host "`nRISK CONTROLS applied to every order`n  Long-only, no leverage, no short selling`n  Max 15,000 USD per position, 45,000 USD total exposure, max 3 positions`n  Stop-loss -5% / take-profit +10% exits`n  Sizing uses REAL account cash, not assumptions`n  Every live order is polled to its final state:`n  filled / partially_filled / canceled / rejected`n" -ForegroundColor Cyan
```

step 15. Seed a position - ONLY if the dry-run said "No orders generated" (skip otherwise)

```powershell
python -c "from alpaca_trading_system.execution import PaperBroker; b = PaperBroker(); r = b.submit_market_order('AAPL', 'buy', 2, dry_run=False); print('SUBMITTED:', r.status, r.order_id); print('FINAL   :', b.wait_for_terminal_status(r))"
```

--> Switch to the browser: refresh the dashboard page after ~10s, AAPL appears in the
account panel. Now UNCHECK Dry-run (a warning appears), click "Run one cycle now":
the strategy sells the non-signaled AAPL position (reason=exit) and the result table
shows status=filled. Also open https://app.alpaca.markets/ (Paper badge) to show the
filled BUY and SELL orders. Optionally click "Start strategy loop" then "Stop
strategy loop" to show loop control.

step 16. Show the structured event log (data updates, signals, orders, fills)

```powershell
Get-Content logs\system.log -Tail 15
```

step 17. Reflection (hold ~35 seconds)

```powershell
Write-Host "`nLIMITATIONS`n  Daily-bar signals only - no intraday reaction, no slippage/cost model`n  Backtest fills at the same close that generated the signal`n  Free IEX feed can differ from consolidated SIP prices`n`nIMPROVEMENTS`n  Websocket streaming quotes, limit orders, richer factor models`n`nWHAT WE LEARNED`n  Most of a real trading system is plumbing - configuration, logging,`n  error handling and order-state tracking - not the strategy formula.`n" -ForegroundColor Cyan
```

step 18. Closing disclaimer (~5 seconds), then stop recording

```powershell
Write-Host "`n   THIS IS PAPER TRADING ONLY - NO REAL MONEY IS USED.   `n" -BackgroundColor DarkRed -ForegroundColor White
```

## PART 2 - After recording (upload the video first, then run these)

step 19. Open README and replace `VIDEO LINK: TODO` with your link

```powershell
notepad README.md
```

step 20. Stage and commit

```powershell
git add README.md
git commit -m "Add video walkthrough link"
```

step 21. Push the branch (first push sets upstream), then open a Pull Request on GitHub

```powershell
git push -u origin fix/review-fixes
```
