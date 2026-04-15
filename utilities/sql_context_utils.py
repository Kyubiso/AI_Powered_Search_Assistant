import json
import re
from pathlib import Path
from typing import Optional

import duckdb


DEFAULT_DATABASE = Path("storage/healthcare.duckdb")
DEFAULT_MANIFEST = Path("metadata/Manifests/datasets_manifest.json")
DEFAULT_TOP_COLUMNS = 25
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "columns",
    "find",
    "for",
    "help",
    "how",
    "in",
    "is",
    "of",
    "or",
    "related",
    "show",
    "that",
    "the",
    "to",
    "what",
    "which",
    "with",
}
BROAD_PROFILE_HINTS = (
    "all symptoms",
    "all side effects",
    "all columns",
    "full profile",
    "complete profile",
    "complete record",
    "entire record",
    "all information",
    "full information",
    "full record",
)
AGGREGATE_HINTS = (
    "how many",
    "count",
    "number of",
    "average",
    "avg",
    "probability",
    "probabilities",
    "prevalence",
    "rate",
    "rates",
    "distribution",
    "minimum",
    "maximum",
    "sum",
    "percentage",
    "percent",
    "group by",
)
IDENTIFIER_COLUMN_NAMES = {
    "id",
    "record_id",
    "dataset_name",
    "disease",
    "diseases",
    "drug",
    "drug_1",
    "drug_2",
    "drug1",
    "drug2",
}


def load_manifest(manifest_path: Path) -> list[dict]:
    with manifest_path.open("r", encoding="utf-8") as manifest_file:
        manifest = json.load(manifest_file)

    if not isinstance(manifest, list):
        raise ValueError("Manifest must be a JSON array of dataset entries.")

    return manifest


def normalize_name(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")

    if not normalized:
        raise ValueError(f"Cannot derive a valid table name from: {value!r}")

    if normalized[0].isdigit():
        normalized = f"dataset_{normalized}"

    return normalized


def build_table_name(entry: dict) -> str:
    explicit_name = str(entry.get("table_name", "")).strip()
    if explicit_name:
        return normalize_name(explicit_name)

    dataset_name = str(entry.get("dataset_name", "")).strip()
    if dataset_name:
        return normalize_name(dataset_name)

    return normalize_name(Path(entry["file_path"]).stem)


def resolve_table_name(
    table_name: Optional[str], dataset_name: Optional[str], manifest: list[dict]
) -> str:
    if table_name:
        return table_name

    if not dataset_name:
        raise ValueError("Provide either --table or --dataset.")

    normalized_dataset_name = dataset_name.strip().lower()
    for entry in manifest:
        current_name = str(entry.get("dataset_name", "")).strip().lower()
        if current_name == normalized_dataset_name:
            return build_table_name(entry)

    raise ValueError(f"Dataset not found in manifest: {dataset_name}")


def list_tables(connection: duckdb.DuckDBPyConnection) -> list[str]:
    rows = connection.execute("SHOW TABLES").fetchall()
    return [table_name for (table_name,) in rows]


def load_schema(connection: duckdb.DuckDBPyConnection, table_name: str) -> list[dict]:
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


def tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 1 and token not in STOPWORDS
    }


def build_token_frequency(schema: list[dict]) -> dict[str, int]:
    frequency = {}
    for column in schema:
        for token in tokenize(column["name"].replace("_", " ")):
            frequency[token] = frequency.get(token, 0) + 1
    return frequency


def score_column(
    column_name: str, question_tokens: set[str], token_frequency: dict[str, int]
) -> float:
    column_tokens = tokenize(column_name.replace("_", " "))
    score = 0.0

    for token in question_tokens:
        if token in column_tokens:
            score += 25.0 / token_frequency.get(token, 1)
        elif any(token in column_token or column_token in token for column_token in column_tokens):
            score += 1.0 / token_frequency.get(token, 1)

    return score


def rank_schema_columns(schema: list[dict], question: str, top_columns: int) -> list[dict]:
    question_tokens = tokenize(question)
    if not question_tokens:
        return schema[:top_columns]

    token_frequency = build_token_frequency(schema)
    scored = []
    for index, column in enumerate(schema):
        score = score_column(column["name"], question_tokens, token_frequency)
        scored.append((score, index, column))

    scored.sort(key=lambda item: (-item[0], item[1]))
    ranked_columns = [column for _, _, column in scored[:top_columns]]

    if all(item[0] == 0 for item in scored[:top_columns]):
        return schema[:top_columns]

    return ranked_columns


def classify_query_mode(question: str) -> str:
    lowered = question.strip().lower()
    has_broad_signal = any(hint in lowered for hint in BROAD_PROFILE_HINTS)
    has_aggregate_signal = any(hint in lowered for hint in AGGREGATE_HINTS)

    if has_broad_signal and has_aggregate_signal:
        return "broad_aggregate"

    if has_broad_signal:
        return "broad_profile"

    if has_aggregate_signal:
        return "aggregate"

    return "focused_filter"


def select_identifier_columns(schema: list[dict]) -> list[dict]:
    selected = []
    for column in schema:
        normalized = normalize_name(column["name"])
        if normalized in IDENTIFIER_COLUMN_NAMES:
            selected.append(column)

    if selected:
        return selected

    return schema[:1]


def merge_columns(primary: list[dict], secondary: list[dict], limit: Optional[int] = None) -> list[dict]:
    seen = set()
    merged = []

    for group in (primary, secondary):
        for column in group:
            name = column["name"]
            if name in seen:
                continue
            seen.add(name)
            merged.append(column)
            if limit is not None and len(merged) >= limit:
                return merged

    return merged


def select_columns_for_query_mode(
    schema: list[dict], question: str, query_mode: str, top_columns: int
) -> list[dict]:
    identifier_columns = select_identifier_columns(schema)

    if query_mode in {"broad_profile", "broad_aggregate"}:
        return merge_columns(identifier_columns, schema)

    ranked_columns = rank_schema_columns(schema, question, top_columns)

    if query_mode == "aggregate":
        return merge_columns(identifier_columns, ranked_columns, limit=top_columns)

    return merge_columns(identifier_columns, ranked_columns, limit=top_columns)
