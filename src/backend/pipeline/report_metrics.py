import argparse
import json
from pathlib import Path

from src.backend.pipeline.metrics_utils import (
    DEFAULT_METRICS_LOG,
    load_query_metrics,
    summarize_query_metrics,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize aggregated query metrics from the local metrics log."
    )
    parser.add_argument(
        "--log-path",
        type=Path,
        default=DEFAULT_METRICS_LOG,
        help=f"Path to the metrics JSONL log. Default: {DEFAULT_METRICS_LOG}",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records = load_query_metrics(args.log_path)
    summary = summarize_query_metrics(records)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
