import argparse
import json
import sys
from pathlib import Path
from typing import Optional

import duckdb

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
        description="Validate and execute a read-only SQL query against DuckDB."
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="SQL query to execute. Optional if --sql-file or --generated-file is used.",
    )
    parser.add_argument(
        "--sql-file",
        type=Path,
        help="Text file containing a SQL query to execute.",
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
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of rows to print from the result. Default: 20",
    )
    return parser.parse_args()


def execute_query(db_path: Path, sql: str, limit: int) -> dict:
    connection = duckdb.connect(str(db_path), read_only=True)
    try:
        result = connection.execute(sql)
        columns = [column[0] for column in result.description] if result.description else []
        rows = result.fetchmany(limit) if columns else []
        return {
            "columns": columns,
            "rows": rows,
            "row_count_returned": len(rows),
            "limit_applied": limit,
        }
    finally:
        connection.close()


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
    validation = validate_sql_query(sql=sql, db_path=args.db_path, expected_table=expected_table)
    if not validation["is_valid"]:
        print(json.dumps({"validation": validation}, indent=2, ensure_ascii=False))
        return 1

    execution = execute_query(args.db_path, validation["normalized_sql"], args.limit)
    output = {
        "validation": validation,
        "execution": execution,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
