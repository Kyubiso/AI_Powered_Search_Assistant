import argparse
from pathlib import Path

from src.backend.data.build_duckdb import (
    DEFAULT_DATABASE,
    build_duckdb_from_manifest_entries,
)
from src.backend.data.generate_dataset_metadata import (
    DEFAULT_MANIFEST,
    DEFAULT_SAMPLE_ROWS,
    filter_manifest,
    generate_metadata_from_manifest_entries,
    load_manifest,
)
from src.backend.data.generate_embeddings import (
    DEFAULT_CHROMA_DIR,
    DEFAULT_COLLECTION,
    DEFAULT_MODEL,
    generate_embeddings_from_manifest_entries,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Refresh backend assets by regenerating metadata, embeddings, and "
            "DuckDB tables from the manifest."
        )
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
            "Only matching manifest entries will be refreshed."
        ),
    )
    parser.add_argument(
        "--chroma-dir",
        type=Path,
        default=DEFAULT_CHROMA_DIR,
        help=f"Persistent ChromaDB directory. Default: {DEFAULT_CHROMA_DIR}",
    )
    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION,
        help=f"ChromaDB collection name. Default: {DEFAULT_COLLECTION}",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"SentenceTransformer embedding model. Default: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"Target DuckDB database file. Default: {DEFAULT_DATABASE}",
    )
    parser.add_argument(
        "--skip-metadata",
        action="store_true",
        help="Skip metadata generation.",
    )
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Skip embedding generation.",
    )
    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Skip DuckDB refresh.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild assets even if they already exist.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = load_manifest(args.manifest)
    manifest = filter_manifest(manifest, args.datasets)

    if not manifest:
        print("No matching datasets found in the manifest.")
        return 1

    if not args.skip_metadata:
        print("Refreshing metadata...")
        generate_metadata_from_manifest_entries(
            manifest=manifest,
            sample_rows=args.sample_rows,
            force=args.force,
        )

    if not args.skip_embeddings:
        print("Refreshing embeddings...")
        generate_embeddings_from_manifest_entries(
            manifest=manifest,
            chroma_dir=args.chroma_dir,
            collection_name=args.collection,
            model_name=args.model,
            force=args.force,
        )

    if not args.skip_db:
        print("Refreshing DuckDB tables...")
        build_duckdb_from_manifest_entries(
            manifest=manifest,
            db_path=args.db_path,
            force=args.force,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
