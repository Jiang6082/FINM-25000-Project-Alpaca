from __future__ import annotations

import argparse
import logging
from pathlib import Path

from alpaca_trading_system.config import load_config
from alpaca_trading_system.engine import collect_loop, collect_once, paper_once, run_backtest_workflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Alpaca paper-trading system CLI")
    parser.add_argument("--config", default="config/config.example.toml")
    subparsers = parser.add_subparsers(dest="command", required=True)

    backtest = subparsers.add_parser("backtest")
    backtest.add_argument("--simulated", action="store_true")
    backtest.add_argument("--output", default="artifacts/backtests/local")

    collect = subparsers.add_parser("collect-once")
    collect.add_argument("--simulated", action="store_true")

    loop = subparsers.add_parser("collect-loop")
    loop.add_argument("--simulated", action="store_true")
    loop.add_argument("--interval", type=int, default=60)
    loop.add_argument("--iterations", type=int, default=None)

    paper = subparsers.add_parser("paper-once")
    paper.add_argument("--dry-run", action="store_true")
    paper.add_argument("--simulated", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_config(args.config)
    config.system.log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=config.system.log_dir / "system.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    if not config.system.paper_trading_only:
        raise SystemExit("Config must keep paper_trading_only=true.")

    if args.command == "backtest":
        output = run_backtest_workflow(config, args.simulated, Path(args.output))
        print("Backtest complete")
        for key, value in output.metrics.items():
            print(f"{key}: {value:.4f}")
        print(f"Saved artifacts to {args.output}")
    elif args.command == "collect-once":
        path = collect_once(config, simulated=args.simulated)
        print(f"Logged market data to {path}")
    elif args.command == "collect-loop":
        print(f"Starting data collection loop every {args.interval}s. Press Ctrl+C to stop.")
        try:
            for path in collect_loop(
                config,
                simulated=args.simulated,
                interval_seconds=args.interval,
                iterations=args.iterations,
            ):
                print(f"Logged market data to {path}")
        except KeyboardInterrupt:
            print("Data collection loop stopped.")
    elif args.command == "paper-once":
        dry_run = args.dry_run or config.execution.dry_run_default
        results = paper_once(config, dry_run=dry_run, simulated=args.simulated)
        print("Paper-trading order decisions:")
        print(results.to_string(index=False) if len(results) else "No orders generated.")


if __name__ == "__main__":
    main()
