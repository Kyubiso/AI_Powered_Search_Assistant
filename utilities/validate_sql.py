import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from sql_validation_utils import (
    DEFAULT_DATABASE,
    DEFAULT_MANIFEST,
    load_generated_payload,
    load_sql_input,
    resolve_expected_table,
    validate_sql_query,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a generated SQL query before executing it."
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="SQL query to validate. Optional if --sql-file or --generated-file is used.",
    )
    parser.add_argument(
        "--sql-file",
        type=Path,
        help="Text file containing a SQL query to validate.",
    )
    parser.add_argument(
        "--generated-file",
        type=Path,
        help="JSON file produced by generate_sql.py.",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"Path to the DuckDB database file. Default: {DEFAULT_DATABASE}",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help=f"Path to the dataset manifest. Default: {DEFAULT_MANIFEST}",
    )
    parser.add_argument(
        "--table",
        help="Expected DuckDB table name.",
    )
    parser.add_argument(
        "--dataset",
        help="Expected dataset name from the manifest.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    generated_payload = load_generated_payload(args.generated_file) if args.generated_file else None
    sql = load_sql_input(query=args.query, sql_file=args.sql_file, generated_payload=generated_payload)
    expected_table = resolve_expected_table(
        manifest_path=args.manifest,
        table_name=args.table,
        dataset_name=args.dataset,
        generated_payload=generated_payload,
    )
    result = validate_sql_query(sql=sql, db_path=args.db_path, expected_table=expected_table)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["is_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
