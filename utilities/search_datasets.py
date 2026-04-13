import argparse
import json
import os
from pathlib import Path

import chromadb
from openai import OpenAI


DEFAULT_CHROMA_DIR = Path("chroma_db")
DEFAULT_COLLECTION = "dataset_metadata"
DEFAULT_MODEL = "text-embedding-3-small"
DEFAULT_TOP_K = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search embedded datasets in ChromaDB using an OpenAI embedding query."
    )
    parser.add_argument("query", help="Natural language query.")
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
        "--top-k",
        type=int,
        default=DEFAULT_TOP_K,
        help=f"Number of results to return. Default: {DEFAULT_TOP_K}",
    )
    return parser.parse_args()


def validate_openai_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set.")


def embed_query(client: OpenAI, model: str, text: str) -> list[float]:
    response = client.embeddings.create(model=model, input=text)
    return response.data[0].embedding


def main() -> int:
    args = parse_args()
    validate_openai_api_key()

    client = OpenAI()
    chroma_client = chromadb.PersistentClient(path=str(args.chroma_dir))
    collection = chroma_client.get_collection(name=args.collection)

    query_embedding = embed_query(client, args.model, args.query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=args.top_k,
    )

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

    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
