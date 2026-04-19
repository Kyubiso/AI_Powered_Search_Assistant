import argparse
import json
from pathlib import Path

import duckdb

from src.backend.sql.sql_context_utils import (
    DEFAULT_DATABASE,
    DEFAULT_MANIFEST,
    DEFAULT_TOP_COLUMNS,
    list_tables,
    load_manifest,
    load_schema,
    rank_schema_columns,
    resolve_table_name,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect DuckDB tables and schema for SQL generation."
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
        help="Exact DuckDB table name to inspect.",
    )
    parser.add_argument(
        "--dataset",
        help="Dataset name from the manifest to inspect.",
    )
    parser.add_argument(
        "--list-tables",
        action="store_true",
        help="List available DuckDB tables and exit.",
    )
    parser.add_argument(
        "--question",
        help=(
            "Optional natural-language question used to rank the most relevant "
            "columns for wide tables."
        ),
    )
    parser.add_argument(
        "--top-columns",
        type=int,
        default=DEFAULT_TOP_COLUMNS,
        help=f"Maximum ranked columns to return when --question is used. Default: {DEFAULT_TOP_COLUMNS}",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.db_path.exists():
        raise FileNotFoundError(f"DuckDB file not found: {args.db_path}")

    manifest = load_manifest(args.manifest)
    connection = duckdb.connect(str(args.db_path), read_only=True)

    try:
        if args.list_tables:
            print(json.dumps({"tables": list_tables(connection)}, indent=2))
            return 0

        table_name = resolve_table_name(args.table, args.dataset, manifest)
        schema = load_schema(connection, table_name)

        output = {
            "table_name": table_name,
            "column_count": len(schema),
            "schema": schema,
        }

        if args.question:
            output["question"] = args.question
            output["suggested_columns"] = rank_schema_columns(
                schema=schema,
                question=args.question,
                top_columns=args.top_columns,
            )

        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
