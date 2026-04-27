import argparse
import json
import os
from pathlib import Path

import duckdb

from src.backend.sql.prepare_sql_generation_context import prepare_sql_generation_context
from src.backend.sql.sql_context_utils import (
    DEFAULT_DATABASE,
    DEFAULT_MANIFEST,
    DEFAULT_TOP_COLUMNS,
)


DEFAULT_MODEL = "gpt-4o-mini"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a candidate read-only SQL query from prepared table context."
    )
    parser.add_argument(
        "question",
        nargs="?",
        help="Natural-language user question. Required unless --context-file is used.",
    )
    parser.add_argument(
        "--context-file",
        type=Path,
        help="Optional JSON file produced by prepare_sql_generation_context.py.",
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
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"OpenAI model used for SQL generation. Default: {DEFAULT_MODEL}",
    )
    return parser.parse_args()


def validate_openai_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set.")


def load_context_from_file(context_file: Path) -> dict:
    with context_file.open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def build_sql_output_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "chosen_candidate_index": {"type": "integer"},
            "chosen_dataset_name": {"type": "string"},
            "suggested_mode": {"type": "string"},
            "final_mode": {"type": "string"},
            "mode_decision": {"type": "string"},
            "table_name": {"type": "string"},
            "scope": {
                "type": "string",
                "enum": ["focused_schema", "broad_schema", "full_schema"],
            },
            "sql": {"type": "string"},
            "selected_columns_used": {
                "type": "array",
                "items": {"type": "string"},
            },
            "explanation": {"type": "string"},
        },
        "required": [
            "chosen_candidate_index",
            "chosen_dataset_name",
            "suggested_mode",
            "final_mode",
            "mode_decision",
            "table_name",
            "scope",
            "sql",
            "selected_columns_used",
            "explanation",
        ],
        "additionalProperties": False,
    }


def build_system_prompt() -> str:
    return (
        "You generate read-only DuckDB SQL queries for a healthcare dataset project. "
        "Return exactly one SQL SELECT statement as JSON. "
        "Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, COPY, ATTACH, DETACH, "
        "PRAGMA, or transaction statements. "
        "Use only the provided candidate datasets, table names, and provided columns. "
        "Do not invent joins, extra tables, or a third dataset outside the candidates. "
        "Always wrap every table name and every column name in double quotes. "
        "This is required even when the identifier looks simple. "
        "Do not wrap SQL in markdown fences. "
        "Do not add LIMIT by default. "
        "Use LIMIT only when the user explicitly asks for a preview, sample, first N rows, "
        "or top N results. "
        "You may keep or override the suggested mode if the schema and question imply a better mode. "
        "You may choose a non-primary candidate when its schema and description fit the question better. "
        "If the question asks for all symptoms or a full profile, include the relevant "
        "identifier column and retrieve the full matching row or columns from the single table. "
        "If the query mode is broad_aggregate, aggregate across the broad column set rather than "
        "returning only a few rows."
    )


def build_user_prompt(context: dict) -> str:
    if "candidates" in context:
        lines = [
            "Generate a single read-only DuckDB SQL query from these retrieved dataset candidates.",
            f"Question: {context['question']}",
            f"Suggested candidate index: {context['suggested_candidate_index']}",
            f"Suggested dataset name: {context['suggested_dataset_name']}",
            "",
            "Candidates:",
        ]

        for candidate in context["candidates"]:
            lines.extend(
                [
                    f"Candidate {candidate['candidate_index']}:",
                    f"- Dataset name: {candidate['dataset_name']}",
                    f"- Table name: {candidate['table_name']}",
                    f"- Source: {candidate.get('source', '')}",
                    f"- Retrieval distance: {candidate.get('distance', '')}",
                    f"- Description: {candidate.get('description', '')}",
                    f"- Suggested mode: {candidate['query_mode']}",
                    f"- Full column count: {candidate['column_count']}",
                    "- Available columns:",
                ]
            )
            for column in candidate["selected_columns"]:
                lines.append(f'  - {column["name"]} ({column["type"]})')
            lines.append("")
    else:
        lines = [
            "Generate a single read-only DuckDB SQL query from this context.",
            f"Question: {context['question']}",
            f"Suggested mode: {context['query_mode']}",
            f"Table name: {context['table_name']}",
            f"Full column count: {context['column_count']}",
            "Available columns:",
        ]

        for column in context["selected_columns"]:
            lines.append(f"- {column['name']} ({column['type']})")

    lines.extend(
        [
            "",
            "Requirements:",
            "- Use exactly one SELECT query.",
            "- Use only one candidate dataset and only that candidate's table and columns.",
            '- Always use double quotes around table names and column names, for example: SELECT "treatment" FROM "mental_health_survey".',
            "- Decide whether the suggested candidate and suggested mode are correct. You may keep them or replace them with a better candidate and final mode.",
            "- Return all necessary matching rows by default. Use LIMIT only when the user explicitly asks for a preview, sample, first N rows, or top N results.",
            "- Do not silently truncate healthcare-relevant results.",
            "- For aggregate questions, use COUNT, AVG, MIN, MAX, SUM, or GROUP BY only when appropriate.",
            "- For broad_aggregate questions, combine broad schema coverage with aggregate expressions such as AVG(...) across the available columns.",
            "- Prefer direct column matches from the schema over indirect inference from loosely related columns.",
            "- For broad profile questions, prefer returning the matching full profile from the same table.",
            "- Assume boolean symptom columns use 1/0 or true/false matching as needed in DuckDB.",
            "- Return chosen_candidate_index as the candidate number you selected.",
            "- Return chosen_dataset_name for the candidate you selected.",
            "- Fill selected_columns_used with the columns actually referenced in the SQL.",
            "- Set scope to focused_schema, broad_schema, or full_schema depending on how much schema coverage the query needs.",
        ]
    )

    return "\n".join(lines)


def generate_sql_response(model: str, context: dict) -> dict:
    from openai import OpenAI

    client = OpenAI()
    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": build_user_prompt(context)},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "sql_generation_response",
                "schema": build_sql_output_schema(),
                "strict": True,
            }
        },
    )

    if response.status == "incomplete":
        reason = getattr(response.incomplete_details, "reason", "unknown")
        raise RuntimeError(f"OpenAI response was incomplete: {reason}")

    if response.output and response.output[0].content[0].type == "refusal":
        refusal_text = response.output[0].content[0].refusal
        raise RuntimeError(f"OpenAI refused the request: {refusal_text}")

    if response.status != "completed":
        raise RuntimeError(f"Unexpected OpenAI response status: {response.status}")

    return json.loads(response.output_text)


def basic_sql_sanity_check(sql: str, table_name: str) -> None:
    normalized = sql.strip().lower()
    if not normalized.startswith("select"):
        raise ValueError("Generated SQL is not a SELECT query.")

    if table_name.lower() not in normalized:
        raise ValueError("Generated SQL does not reference the expected table.")


def verify_context_tables(context: dict, db_path: Path) -> None:
    if "candidates" in context:
        for candidate in context["candidates"]:
            verify_table_exists(db_path, candidate["table_name"])
        return

    verify_table_exists(db_path, context["table_name"])


def resolve_generated_table(context: dict, generated: dict) -> str:
    table_name = generated["table_name"]

    if "candidates" not in context:
        return table_name

    allowed_candidates = {
        candidate["candidate_index"]: candidate for candidate in context["candidates"]
    }
    chosen_index = generated["chosen_candidate_index"]
    if chosen_index not in allowed_candidates:
        raise ValueError(f"Generated candidate index is not allowed: {chosen_index}")

    chosen_candidate = allowed_candidates[chosen_index]
    if chosen_candidate["table_name"] != table_name:
        raise ValueError(
            "Generated table name does not match the chosen candidate table: "
            f"{table_name}"
        )

    return table_name


def generate_sql_payload(model: str, context: dict, db_path: Path) -> dict:
    verify_context_tables(context, db_path)
    generated = generate_sql_response(model, context)
    expected_table = resolve_generated_table(context, generated)
    basic_sql_sanity_check(generated["sql"], expected_table)

    return {
        "question": context["question"],
        "suggested_mode": context.get("query_mode"),
        "table_name": expected_table,
        "sql_generation_model": model,
        "selected_columns": context.get("selected_columns"),
        "candidate_contexts": context.get("candidates"),
        "generated_query": generated,
    }


def prepare_context_from_args(args: argparse.Namespace) -> dict:
    if not args.question:
        raise ValueError("Question is required unless --context-file is provided.")

    return prepare_sql_generation_context(
        question=args.question,
        db_path=args.db_path,
        manifest_path=args.manifest,
        table_name=args.table,
        dataset_name=args.dataset,
        top_columns=args.top_columns,
    )


def verify_table_exists(db_path: Path, table_name: str) -> None:
    connection = duckdb.connect(str(db_path), read_only=True)
    try:
        result = connection.execute("SHOW TABLES").fetchall()
        existing_tables = {name for (name,) in result}
        if table_name not in existing_tables:
            raise ValueError(f"Table not found in DuckDB: {table_name}")
    finally:
        connection.close()


def main() -> int:
    args = parse_args()
    validate_openai_api_key()

    if args.context_file:
        context = load_context_from_file(args.context_file)
    else:
        context = prepare_context_from_args(args)

    output = generate_sql_payload(model=args.model, context=context, db_path=args.db_path)
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
