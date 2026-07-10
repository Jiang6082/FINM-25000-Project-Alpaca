from alpaca_trading_system.backtest import run_backtest
from alpaca_trading_system.config import load_config
from alpaca_trading_system.data import SimulatedMarketData


def test_backtest_outputs_metrics_and_artifacts_data():
    config = load_config()
    bars = SimulatedMarketData(seed=12).fetch_bars(config.tickers, lookback_days=160)
    output = run_backtest(bars, config)
    assert len(output.equity) > 50
    assert output.equity.iloc[-1] > 0
    assert "total_return" in output.metrics
    assert "max_drawdown" in output.metrics
    assert {"timestamp", "symbol", "signal"}.issubset(output.signals.columns)
