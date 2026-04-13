import argparse
import json
import os
from pathlib import Path

import chromadb
from openai import OpenAI


DEFAULT_MANIFEST = Path("metadata/Manifests/datasets_manifest.json")
DEFAULT_CHROMA_DIR = Path("chroma_db")
DEFAULT_COLLECTION = "dataset_metadata"
DEFAULT_MODEL = "text-embedding-3-small"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate OpenAI embeddings from dataset metadata and store them in ChromaDB."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help=f"Path to the dataset manifest. Default: {DEFAULT_MANIFEST}",
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
        help=f"OpenAI embedding model. Default: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--dataset",
        action="append",
        dest="datasets",
        help=(
            "Optional dataset name filter. Can be passed multiple times. "
            "Only matching manifest entries will be embedded."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-embed datasets even if they already exist in ChromaDB.",
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


def load_metadata(metadata_path: Path) -> dict:
    with metadata_path.open("r", encoding="utf-8") as metadata_file:
        return json.load(metadata_file)


def build_document(metadata: dict) -> str:
    return metadata["embedding_text"]


def build_record_id(metadata: dict) -> str:
    return Path(metadata["file_path"]).stem


def validate_openai_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set.")


def embed_text(client: OpenAI, model: str, text: str) -> list[float]:
    response = client.embeddings.create(model=model, input=text)
    return response.data[0].embedding


def upsert_metadata(
    collection,
    metadata: dict,
    embedding: list[float],
) -> None:
    record_id = build_record_id(metadata)
    collection.upsert(
        ids=[record_id],
        embeddings=[embedding],
        documents=[metadata["embedding_text"]],
        metadatas=[
            {
                "dataset_name": metadata["dataset_name"],
                "file_path": metadata["file_path"],
                "source": metadata.get("source", ""),
                "domain": metadata.get("domain", ""),
                "num_rows": metadata["num_rows"],
                "num_columns": metadata["num_columns"],
            }
        ],
    )


def should_skip(collection, record_id: str, force: bool) -> bool:
    if force:
        return False

    existing = collection.get(ids=[record_id])
    return bool(existing["ids"])


def main() -> int:
    args = parse_args()
    validate_openai_api_key()

    manifest = load_manifest(args.manifest)
    manifest = filter_manifest(manifest, args.datasets)
    if not manifest:
        print("No matching datasets found in the manifest.")
        return 1

    client = OpenAI()
    chroma_client = chromadb.PersistentClient(path=str(args.chroma_dir))
    collection = chroma_client.get_or_create_collection(
        name=args.collection,
        metadata={"hnsw:space": "cosine"},
    )

    for entry in manifest:
        metadata_path = Path(entry["metadata_path"])
        metadata = load_metadata(metadata_path)
        record_id = build_record_id(metadata)

        if should_skip(collection, record_id, args.force):
            print(f"Skipping existing embedding: {record_id}")
            continue

        document = build_document(metadata)
        embedding = embed_text(client, args.model, document)
        upsert_metadata(collection, metadata, embedding)
        print(f"Embedded dataset: {metadata['dataset_name']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
