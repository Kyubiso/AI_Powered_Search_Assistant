import argparse
import json
from pathlib import Path

from src.backend.retrieval.retrieve_sql_context import (
    DEFAULT_CHROMA_DIR,
    DEFAULT_COLLECTION,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_MANIFEST,
    DEFAULT_DATABASE,
    enrich_with_duckdb_context,
    load_manifest,
    retrieve_datasets,
)
from src.backend.sql.generate_sql import DEFAULT_MODEL, generate_sql_payload
from src.backend.sql.prepare_sql_context import prepare_sql_context
from src.backend.sql.run_sql_query import execute_query
from src.backend.sql.sql_context_utils import DEFAULT_TOP_COLUMNS
from src.backend.sql.sql_validation_utils import validate_sql_query


DEFAULT_SQL_TOP_K = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "End-to-end pipeline: retrieve a dataset, prepare SQL context, generate SQL, "
            "validate it, and execute it."
        )
    )
    parser.add_argument("question", help="Natural-language user question.")
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
        "--retrieval-model",
        default=DEFAULT_EMBEDDING_MODEL,
        help=f"OpenAI embedding model for retrieval. Default: {DEFAULT_EMBEDDING_MODEL}",
    )
    parser.add_argument(
        "--sql-model",
        default=DEFAULT_MODEL,
        help=f"OpenAI model used for SQL generation. Default: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--retrieval-top-k",
        type=int,
        default=DEFAULT_SQL_TOP_K,
        help=f"Number of retrieved datasets to inspect. Default: {DEFAULT_SQL_TOP_K}",
    )
    parser.add_argument(
        "--top-columns",
        type=int,
        default=DEFAULT_TOP_COLUMNS,
        help=f"Maximum compact columns for focused modes. Default: {DEFAULT_TOP_COLUMNS}",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of rows to return from execution. Default: 20",
    )
    return parser.parse_args()


def select_best_dataset(retrieved_with_context: list[dict]) -> dict:
    if not retrieved_with_context:
        raise ValueError("No retrieved datasets were available for SQL generation.")
    return retrieved_with_context[0]


def build_pipeline_output(
    question: str,
    retrieved_candidates: list[dict],
    selected_dataset: dict,
    sql_context: dict,
    generated_payload: dict,
    validation: dict,
    execution: dict,
) -> dict:
    return {
        "question": question,
        "retrieved_candidates": [
            {
                "dataset_name": item.get("dataset_name"),
                "table_name": item.get("table_name"),
                "distance": item.get("distance"),
                "source": item.get("source"),
            }
            for item in retrieved_candidates
        ],
        "selected_dataset": {
            "dataset_name": selected_dataset.get("dataset_name"),
            "table_name": selected_dataset.get("table_name"),
            "source": selected_dataset.get("source"),
            "distance": selected_dataset.get("distance"),
        },
        "sql_context": sql_context,
        "generated_sql": generated_payload["generated_query"],
        "validation": validation,
        "execution": execution,
    }


def main() -> int:
    args = parse_args()
    manifest = load_manifest(args.manifest)

    retrieved = retrieve_datasets(
        query=args.question,
        chroma_dir=args.chroma_dir,
        collection_name=args.collection,
        model=args.retrieval_model,
        top_k=args.retrieval_top_k,
    )
    retrieved_with_context = enrich_with_duckdb_context(retrieved, manifest, args.db_path)
    selected_dataset = select_best_dataset(retrieved_with_context)

    sql_context = prepare_sql_context(
        question=args.question,
        db_path=args.db_path,
        manifest_path=args.manifest,
        table_name=selected_dataset["table_name"],
        top_columns=args.top_columns,
    )
    generated_payload = generate_sql_payload(
        model=args.sql_model,
        context=sql_context,
        db_path=args.db_path,
    )

    validation = validate_sql_query(
        sql=generated_payload["generated_query"]["sql"],
        db_path=args.db_path,
        expected_table=sql_context["table_name"],
    )
    if not validation["is_valid"]:
        output = build_pipeline_output(
            question=args.question,
            retrieved_candidates=retrieved_with_context,
            selected_dataset=selected_dataset,
            sql_context=sql_context,
            generated_payload=generated_payload,
            validation=validation,
            execution=None,
        )
        print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
        return 1

    execution = execute_query(
        db_path=args.db_path,
        sql=validation["normalized_sql"],
        limit=args.limit,
    )
    output = build_pipeline_output(
        question=args.question,
        retrieved_candidates=retrieved_with_context,
        selected_dataset=selected_dataset,
        sql_context=sql_context,
        generated_payload=generated_payload,
        validation=validation,
        execution=execution,
    )
    print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
