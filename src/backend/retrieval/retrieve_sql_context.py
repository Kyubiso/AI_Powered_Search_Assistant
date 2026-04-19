import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Optional

import duckdb

from src.backend.sql.sql_context_utils import DEFAULT_DATABASE, DEFAULT_MANIFEST

DEFAULT_CHROMA_DIR = Path("chroma_db")
DEFAULT_COLLECTION = "dataset_metadata"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_TOP_K = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Retrieve relevant datasets from ChromaDB and enrich them with "
            "DuckDB table/schema context for later SQL generation."
        )
    )
    parser.add_argument("query", help="Natural language user question.")
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
        help=f"Path to the DuckDB database file. Default: {DEFAULT_DATABASE}",
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
        default=DEFAULT_EMBEDDING_MODEL,
        help=f"OpenAI embedding model. Default: {DEFAULT_EMBEDDING_MODEL}",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_TOP_K,
        help=f"Number of retrieved datasets to enrich. Default: {DEFAULT_TOP_K}",
    )
    return parser.parse_args()


def validate_openai_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set.")


def load_manifest(manifest_path: Path) -> list[dict]:
    with manifest_path.open("r", encoding="utf-8") as manifest_file:
        manifest = json.load(manifest_file)

    if not isinstance(manifest, list):
        raise ValueError("Manifest must be a JSON array of dataset entries.")

    return manifest


def embed_query(client: Any, model: str, text: str) -> list[float]:
    response = client.embeddings.create(model=model, input=text)
    return response.data[0].embedding


def retrieve_datasets(
    query: str,
    chroma_dir: Path,
    collection_name: str,
    model: str,
    top_k: int,
) -> list[dict]:
    import chromadb
    from openai import OpenAI

    validate_openai_api_key()

    client = OpenAI()
    chroma_client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = chroma_client.get_collection(name=collection_name)

    query_embedding = embed_query(client, model, query)
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)

    output = []
    for record_id, document, metadata, distance in zip(
        results["ids"][0],
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        output.append(
            {
                "id": record_id,
                "distance": distance,
                "dataset_name": metadata.get("dataset_name"),
                "file_path": metadata.get("file_path"),
                "domain": metadata.get("domain"),
                "source": metadata.get("source"),
                "embedding_text": document,
            }
        )

    return output


def find_manifest_entry(manifest: list[dict], file_path: str) -> Optional[dict]:
    for entry in manifest:
        if str(entry.get("file_path", "")).strip() == str(file_path).strip():
            return entry
    return None


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


def load_table_schema(connection: duckdb.DuckDBPyConnection, table_name: str) -> list[dict]:
    rows = connection.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'main' AND table_name = ?
        ORDER BY ordinal_position
        """,
        [table_name],
    ).fetchall()

    if not rows:
        raise ValueError(f"Table not found in DuckDB: {table_name}")

    return [{"name": column_name, "type": data_type} for column_name, data_type in rows]


def enrich_with_duckdb_context(
    retrieved: list[dict], manifest: list[dict], db_path: Path
) -> list[dict]:
    if not db_path.exists():
        raise FileNotFoundError(f"DuckDB file not found: {db_path}")

    connection = duckdb.connect(str(db_path), read_only=True)
    try:
        output = []
        for item in retrieved:
            manifest_entry = find_manifest_entry(manifest, item["file_path"])
            if manifest_entry is None:
                raise ValueError(
                    "Retrieved dataset was not found in the manifest: "
                    f"{item['file_path']}"
                )

            table_name = build_table_name(manifest_entry)
            schema = load_table_schema(connection, table_name)

            enriched_item = dict(item)
            enriched_item["table_name"] = table_name
            enriched_item["schema"] = schema
            output.append(enriched_item)

        return output
    finally:
        connection.close()


def main() -> int:
    args = parse_args()
    manifest = load_manifest(args.manifest)
    retrieved = retrieve_datasets(
        query=args.query,
        chroma_dir=args.chroma_dir,
        collection_name=args.collection,
        model=args.model,
        top_k=args.top_k,
    )
    enriched = enrich_with_duckdb_context(retrieved, manifest, args.db_path)
    print(json.dumps(enriched, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
