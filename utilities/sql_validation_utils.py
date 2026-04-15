import json
import re
import sys
from pathlib import Path
from typing import Optional

import duckdb

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from sql_context_utils import DEFAULT_DATABASE, DEFAULT_MANIFEST, load_manifest, resolve_table_name


FORBIDDEN_KEYWORDS = (
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "copy",
    "attach",
    "detach",
    "pragma",
    "truncate",
    "merge",
    "replace",
    "grant",
    "revoke",
    "call",
)


def load_generated_payload(payload_path: Path) -> dict:
    with payload_path.open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def resolve_expected_table(
    manifest_path: Path = DEFAULT_MANIFEST,
    table_name: Optional[str] = None,
    dataset_name: Optional[str] = None,
    generated_payload: Optional[dict] = None,
) -> Optional[str]:
    if generated_payload:
        if generated_payload.get("table_name"):
            return generated_payload["table_name"]
        generated_query = generated_payload.get("generated_query", {})
        if generated_query.get("table_name"):
            return generated_query["table_name"]

    if table_name:
        return table_name

    if dataset_name:
        manifest = load_manifest(manifest_path)
        return resolve_table_name(table_name=None, dataset_name=dataset_name, manifest=manifest)

    return None


def load_sql_input(
    query: Optional[str] = None,
    sql_file: Optional[Path] = None,
    generated_payload: Optional[dict] = None,
) -> str:
    if query:
        return query.strip()

    if sql_file:
        return sql_file.read_text(encoding="utf-8").strip()

    if generated_payload:
        generated_query = generated_payload.get("generated_query", {})
        sql = generated_query.get("sql")
        if sql:
            return str(sql).strip()

    raise ValueError("No SQL input provided.")


def strip_quoted_content(sql: str) -> str:
    sql = re.sub(r"'(?:''|[^'])*'", "''", sql)
    sql = re.sub(r'"(?:""|[^"])*"', '""', sql)
    return sql


def has_multiple_statements(sql: str) -> bool:
    in_single = False
    in_double = False

    for index, char in enumerate(sql):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == ";" and not in_single and not in_double:
            tail = sql[index + 1 :].strip()
            if tail:
                return True

    return False


def extract_from_clause(sql: str) -> str:
    pattern = re.compile(
        r"\bfrom\b(?P<clause>.*?)(\bwhere\b|\bgroup\s+by\b|\border\s+by\b|\blimit\b|\bhaving\b|$)",
        flags=re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(sql)
    if not match:
        return ""
    return match.group("clause").strip()


def extract_from_tables(sql: str) -> list[str]:
    pattern = re.compile(r"\bfrom\s+([a-zA-Z_][a-zA-Z0-9_]*)", flags=re.IGNORECASE)
    return pattern.findall(sql)


def validate_sql_query(
    sql: str,
    db_path: Path = DEFAULT_DATABASE,
    expected_table: Optional[str] = None,
) -> dict:
    violations = []
    stripped_sql = sql.strip()
    normalized_sql = stripped_sql.rstrip(";").strip()
    lowered_sql = strip_quoted_content(normalized_sql).lower()

    if not normalized_sql:
        violations.append("SQL query is empty.")
    if "--" in lowered_sql or "/*" in lowered_sql or "*/" in lowered_sql:
        violations.append("SQL comments are not allowed.")
    if has_multiple_statements(stripped_sql):
        violations.append("Multiple SQL statements are not allowed.")
    if not lowered_sql.startswith("select"):
        violations.append("Only SELECT queries are allowed.")

    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", lowered_sql):
            violations.append(f"Forbidden SQL keyword detected: {keyword}")

    if re.search(r"\bjoin\b", lowered_sql):
        violations.append("JOIN queries are not allowed in the current phase.")

    from_clause = extract_from_clause(lowered_sql)
    if from_clause and "," in from_clause:
        violations.append("Multiple tables in FROM are not allowed.")

    from_tables = extract_from_tables(lowered_sql)
    if len(from_tables) != 1:
        violations.append("Exactly one table must appear in the FROM clause.")
    elif expected_table and from_tables[0] != expected_table.lower():
        violations.append(
            f"Query references unexpected table '{from_tables[0]}', expected '{expected_table}'."
        )

    syntax_ok = False
    explain_error = None
    if not violations:
        connection = duckdb.connect(str(db_path), read_only=True)
        try:
            connection.execute(f"EXPLAIN {normalized_sql}")
            syntax_ok = True
        except Exception as exc:
            explain_error = str(exc)
            violations.append(f"DuckDB rejected the query: {exc}")
        finally:
            connection.close()

    return {
        "is_valid": not violations,
        "normalized_sql": normalized_sql,
        "expected_table": expected_table,
        "detected_tables": from_tables,
        "syntax_ok": syntax_ok,
        "violations": violations,
        "explain_error": explain_error,
    }
