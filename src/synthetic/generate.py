"""
Synthetic data generator — CLI entry point.

Wraps the NCR Atleos reference generator (ncr_generator.py) and exposes
a consistent CLI interface for the project pipeline.

Usage:
    python -m src.synthetic.generate
    python -m src.synthetic.generate --output-dir data/synthetic
    python -m src.synthetic.generate --output-dir data/synthetic --seed 42
"""
from __future__ import annotations

import argparse
from pathlib import Path

from src.synthetic import ncr_generator


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate 24-hour synthetic ATM log data for all 7 sources."
    )
    parser.add_argument(
        "--output-dir",
        default="data/synthetic",
        help="Directory to write output files into (default: data/synthetic)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="RNG seed for reproducibility (default: 42)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ncr_generator.main(output_dir=str(output_dir), seed=args.seed)


if __name__ == "__main__":
    main()
