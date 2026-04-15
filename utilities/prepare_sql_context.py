import argparse
import json
from pathlib import Path

import duckdb

from sql_context_utils import (
    DEFAULT_DATABASE,
    DEFAULT_MANIFEST,
    DEFAULT_TOP_COLUMNS,
    classify_query_mode,
    load_manifest,
    load_schema,
    resolve_table_name,
    select_columns_for_query_mode,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare table and schema context for later text-to-SQL generation."
    )
    parser.add_argument("question", help="Natural-language user question.")
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
        help="Exact DuckDB table name to prepare context for.",
    )
    parser.add_argument(
        "--dataset",
        help="Dataset name from the manifest to prepare context for.",
    )
    parser.add_argument(
        "--top-columns",
        type=int,
        default=DEFAULT_TOP_COLUMNS,
        help=f"Maximum compact columns for focused modes. Default: {DEFAULT_TOP_COLUMNS}",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.db_path.exists():
        raise FileNotFoundError(f"DuckDB file not found: {args.db_path}")

    manifest = load_manifest(args.manifest)
    table_name = resolve_table_name(args.table, args.dataset, manifest)
    query_mode = classify_query_mode(args.question)

    connection = duckdb.connect(str(args.db_path), read_only=True)
    try:
        full_schema = load_schema(connection, table_name)
    finally:
        connection.close()

    selected_columns = select_columns_for_query_mode(
        schema=full_schema,
        question=args.question,
        query_mode=query_mode,
        top_columns=args.top_columns,
    )

    output = {
        "question": args.question,
        "query_mode": query_mode,
        "table_name": table_name,
        "column_count": len(full_schema),
        "selected_column_count": len(selected_columns),
        "selected_columns": selected_columns,
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
