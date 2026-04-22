import argparse
import json
from pathlib import Path

import pandas as pd


DEFAULT_MANIFEST = Path("metadata/Manifests/datasets_manifest.json")
DEFAULT_SAMPLE_ROWS = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate dataset metadata JSON files from the manifest and local CSV files."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help=f"Path to the dataset manifest. Default: {DEFAULT_MANIFEST}",
    )
    parser.add_argument(
        "--sample-rows",
        type=int,
        default=DEFAULT_SAMPLE_ROWS,
        help=f"Number of sample rows to store in metadata. Default: {DEFAULT_SAMPLE_ROWS}",
    )
    parser.add_argument(
        "--dataset",
        action="append",
        dest="datasets",
        help=(
            "Optional dataset name filter. Can be passed multiple times. "
            "Only matching manifest entries will be processed."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate metadata even if the target metadata file already exists.",
    )
    return parser.parse_args()


def load_manifest(manifest_path: Path) -> list[dict]:
    with manifest_path.open("r", encoding="utf-8") as manifest_file:
        manifest = json.load(manifest_file)

    if not isinstance(manifest, list):
        raise ValueError("Manifest must be a JSON array of dataset entries.")

    return manifest


def filter_manifest(manifest: list[dict], dataset_filters: list[str] | None) -> list[dict]:
    if not dataset_filters:
        return manifest

    allowed = {name.strip().lower() for name in dataset_filters}
    return [
        entry
        for entry in manifest
        if str(entry.get("dataset_name", "")).strip().lower() in allowed
    ]


def build_metadata(entry: dict, sample_rows: int) -> dict:
    file_path = Path(entry["file_path"])
    normalized_file_path = file_path.as_posix()
    df = pd.read_csv(file_path)

    dataset_name = entry.get("dataset_name") or file_path.stem
    source = entry.get("source", "")
    domain = entry.get("domain", "")
    manifest_description = entry.get("description", "").strip()
    data_interpretation_notes = entry.get("data_interpretation_notes", "").strip()

    metadata = {
        "dataset_name": dataset_name,
        "source": source,
        "file_path": normalized_file_path,
        "num_rows": int(len(df)),
        "num_columns": int(len(df.columns)),
        "columns": df.columns.tolist(),
        "sample_rows": df.head(sample_rows).to_dict(orient="records"),
        "domain": domain,
        "data_interpretation_notes": data_interpretation_notes,
        "description": build_description(
            dataset_name=dataset_name,
            manifest_description=manifest_description,
            num_rows=len(df),
            num_columns=len(df.columns),
        ),
        "embedding_text": build_embedding_text(
            dataset_name=dataset_name,
            source=source,
            domain=domain,
            manifest_description=manifest_description,
            data_interpretation_notes=data_interpretation_notes,
            columns=df.columns.tolist(),
            num_rows=len(df),
            num_columns=len(df.columns),
        ),
    }
    return metadata


def build_description(
    dataset_name: str,
    manifest_description: str,
    num_rows: int,
    num_columns: int,
) -> str:
    structure_summary = (
        f"It contains {num_rows:,} rows and {num_columns} columns in CSV format."
    )

    if manifest_description:
        return f"{manifest_description} {structure_summary}"

    return f"{dataset_name} is a healthcare dataset. {structure_summary}"


def build_embedding_text(
    dataset_name: str,
    source: str,
    domain: str,
    manifest_description: str,
    data_interpretation_notes: str,
    columns: list[str],
    num_rows: int,
    num_columns: int,
) -> str:
    column_preview = ", ".join(columns[:15])
    if len(columns) > 15:
        column_preview += ", ..."

    parts = [
        f"Dataset: {dataset_name}.",
        f"Source: {source or 'local CSV file'}.",
        f"Domain: {domain or 'healthcare'}.",
        f"Rows: {num_rows}.",
        f"Columns: {num_columns}.",
    ]

    if manifest_description:
        parts.append(f"Description: {manifest_description}")

    if data_interpretation_notes:
        parts.append(f"Data interpretation notes: {data_interpretation_notes}")

    parts.append(f"Column preview: {column_preview}.")
    parts.append(
        "Use this dataset for retrieval, metadata search, and question answering over local healthcare data."
    )

    return " ".join(parts)


def save_metadata(metadata: dict, metadata_path: Path) -> None:
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with metadata_path.open("w", encoding="utf-8") as metadata_file:
        json.dump(metadata, metadata_file, indent=2, ensure_ascii=False)


def validate_entry(entry: dict) -> None:
    required_fields = ["file_path", "metadata_path"]
    for field in required_fields:
        if not entry.get(field):
            raise ValueError(f"Manifest entry is missing required field: {field}")


def main() -> int:
    args = parse_args()
    manifest = load_manifest(args.manifest)
    manifest = filter_manifest(manifest, args.datasets)

    if not manifest:
        print("No matching datasets found in the manifest.")
        return 1

    for entry in manifest:
        validate_entry(entry)
        metadata_path = Path(entry["metadata_path"])
        if metadata_path.exists() and not args.force:
            print(f"Skipping existing metadata: {entry['metadata_path']}")
            continue

        metadata = build_metadata(entry, args.sample_rows)
        save_metadata(metadata, metadata_path)
        print(f"Generated metadata: {entry['metadata_path']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
