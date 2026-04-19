import argparse
import json
import re
from pathlib import Path
from typing import Optional

import duckdb


DEFAULT_MANIFEST = Path("metadata/Manifests/datasets_manifest.json")
DEFAULT_DATABASE = Path("storage/healthcare.duckdb")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a local DuckDB database from manifest-listed CSV datasets."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help=f"Path to the dataset manifest. Default: {DEFAULT_MANIFEST}",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"Target DuckDB database file. Default: {DEFAULT_DATABASE}",
    )
    parser.add_argument(
        "--dataset",
        action="append",
        dest="datasets",
        help=(
            "Optional dataset name filter. Can be passed multiple times. "
            "Only matching manifest entries will be imported."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild tables even if they already exist in DuckDB.",
    )
    return parser.parse_args()


def load_manifest(manifest_path: Path) -> list[dict]:
    with manifest_path.open("r", encoding="utf-8") as manifest_file:
        manifest = json.load(manifest_file)

    if not isinstance(manifest, list):
        raise ValueError("Manifest must be a JSON array of dataset entries.")

    return manifest


def filter_manifest(
    manifest: list[dict], dataset_filters: Optional[list[str]]
) -> list[dict]:
    if not dataset_filters:
        return manifest

    allowed = {name.strip().lower() for name in dataset_filters}
    return [
        entry
        for entry in manifest
        if str(entry.get("dataset_name", "")).strip().lower() in allowed
    ]


def validate_entry(entry: dict) -> None:
    if not entry.get("file_path"):
        raise ValueError("Manifest entry is missing required field: file_path")


def build_table_name(entry: dict) -> str:
    explicit_name = str(entry.get("table_name", "")).strip()
    if explicit_name:
        return normalize_name(explicit_name)

    dataset_name = str(entry.get("dataset_name", "")).strip()
    if dataset_name:
        return normalize_name(dataset_name)

    file_path = Path(entry["file_path"])
    return normalize_name(file_path.stem)


def normalize_name(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")

    if not normalized:
        raise ValueError(f"Cannot derive a valid table name from: {value!r}")

    if normalized[0].isdigit():
        normalized = f"dataset_{normalized}"

    return normalized


def table_exists(connection: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    result = connection.execute(
        """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'main' AND table_name = ?
        LIMIT 1
        """,
        [table_name],
    ).fetchone()
    return result is not None


def import_dataset(
    connection: duckdb.DuckDBPyConnection,
    csv_path: Path,
    table_name: str,
    force: bool,
) -> str:
    if table_exists(connection, table_name):
        if not force:
            return f"Skipping existing table: {table_name}"
        connection.execute(f'DROP TABLE "{table_name}"')

    connection.execute(
        f'''
        CREATE TABLE "{table_name}" AS
        SELECT *
        FROM read_csv_auto(?, HEADER = TRUE)
        ''',
        [str(csv_path)],
    )
    return f"Imported dataset into table: {table_name}"


def main() -> int:
    args = parse_args()
    manifest = load_manifest(args.manifest)
    manifest = filter_manifest(manifest, args.datasets)

    if not manifest:
        print("No matching datasets found in the manifest.")
        return 1

    args.db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(args.db_path))

    try:
        for entry in manifest:
            validate_entry(entry)
            csv_path = Path(entry["file_path"])
            if not csv_path.exists():
                raise FileNotFoundError(f"CSV file not found: {csv_path}")

            table_name = build_table_name(entry)
            message = import_dataset(
                connection=connection,
                csv_path=csv_path,
                table_name=table_name,
                force=args.force,
            )
            print(message)
    finally:
        connection.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
