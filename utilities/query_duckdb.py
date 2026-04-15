import argparse
import json
from pathlib import Path
from typing import Optional

import duckdb


DEFAULT_DATABASE = Path("storage/healthcare.duckdb")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a SQL query against the local DuckDB database."
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="SQL query to execute. If omitted, the script will prompt for one.",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"Path to the DuckDB database file. Default: {DEFAULT_DATABASE}",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of rows to print from the result. Default: 20",
    )
    return parser.parse_args()


def read_query(query_arg: Optional[str]) -> str:
    if query_arg:
        return query_arg.strip()

    return input("Enter SQL query: ").strip()


def main() -> int:
    args = parse_args()
    query = read_query(args.query)

    if not query:
        print("No query provided.")
        return 1

    if not args.db_path.exists():
        print(f"DuckDB file not found: {args.db_path}")
        return 1

    try:
        connection = duckdb.connect(str(args.db_path), read_only=True)
    except duckdb.IOException as exc:
        print("Could not open the DuckDB file.")
        print(
            "Another application may already be using it. Close tools like "
            "DataGrip, DBeaver, or VS Code database extensions and try again."
        )
        print(f"Details: {exc}")
        return 1

    try:
        result = connection.execute(query)

        if result.description is None:
            print("Query executed successfully.")
            return 0

        columns = [column[0] for column in result.description]
        rows = result.fetchmany(args.limit)

        print(json.dumps({"columns": columns, "rows": rows}, indent=2, default=str))
        if len(rows) == args.limit:
            print(f"\nShowing first {args.limit} rows.")
    finally:
        connection.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
