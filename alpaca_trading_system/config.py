from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class SystemConfig:
    mode: str
    paper_trading_only: bool
    log_dir: Path
    data_dir: Path


@dataclass(frozen=True)
class StrategyConfig:
    name: str
    fast_window: int
    slow_window: int
    breakout_window: int
    volatility_window: int
    max_symbols: int


@dataclass(frozen=True)
class RiskConfig:
    initial_capital: float
    max_position_notional: float
    max_total_notional: float
    max_open_positions: int
    stop_loss_pct: float
    take_profit_pct: float
    allow_short: bool
    allow_leverage: bool


@dataclass(frozen=True)
class ExecutionConfig:
    order_type: str
    time_in_force: str
    dry_run_default: bool


@dataclass(frozen=True)
class AppConfig:
    system: SystemConfig
    tickers: list[str]
    strategy: StrategyConfig
    risk: RiskConfig
    execution: ExecutionConfig


def load_config(path: str | Path = "config/config.example.toml") -> AppConfig:
    raw = tomllib.loads(Path(path).read_text())
    return AppConfig(
        system=SystemConfig(
            mode=raw["system"]["mode"],
            paper_trading_only=bool(raw["system"]["paper_trading_only"]),
            log_dir=Path(raw["system"]["log_dir"]),
            data_dir=Path(raw["system"]["data_dir"]),
        ),
        tickers=[ticker.upper() for ticker in raw["universe"]["tickers"]],
        strategy=StrategyConfig(**raw["strategy"]),
        risk=RiskConfig(**raw["risk"]),
        execution=ExecutionConfig(**raw["execution"]),
    )
