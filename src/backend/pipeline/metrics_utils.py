import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional


DEFAULT_METRICS_LOG = Path("storage/metrics/query_metrics.jsonl")


def now_utc_iso() -> str:
    return datetime.now(UTC).isoformat()


def elapsed_ms(start_time: float, end_time: float) -> float:
    return round((end_time - start_time) * 1000.0, 3)


def _safe_round(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return round(float(value), 3)


def _candidate_lookup(sql_context: dict) -> dict[int, dict]:
    lookup = {}
    for candidate in sql_context.get("candidates", []):
        lookup[candidate["candidate_index"]] = candidate
    return lookup


def build_query_metrics(
    question: str,
    sql_context: Optional[dict],
    generated_payload: Optional[dict],
    validation: Optional[dict],
    execution: Optional[dict],
    stage_timings_ms: dict[str, float],
    total_elapsed_ms: float,
    status: str,
    error_message: Optional[str] = None,
) -> dict:
    generated_query = (generated_payload or {}).get("generated_query", {})
    candidate_lookup = _candidate_lookup(sql_context or {})

    suggested_candidate_index = (sql_context or {}).get("suggested_candidate_index")
    chosen_candidate_index = generated_query.get("chosen_candidate_index")
    suggested_candidate = candidate_lookup.get(suggested_candidate_index)
    chosen_candidate = candidate_lookup.get(chosen_candidate_index)

    suggested_mode = chosen_candidate.get("query_mode") if chosen_candidate else None
    final_mode = generated_query.get("final_mode")

    candidate_changed_by_model = (
        suggested_candidate_index is not None
        and chosen_candidate_index is not None
        and chosen_candidate_index != suggested_candidate_index
    )
    mode_changed_by_model = bool(
        suggested_mode and final_mode and suggested_mode != final_mode
    )

    metrics = {
        "recorded_at": now_utc_iso(),
        "question": question,
        "status": status,
        "error_message": error_message,
        "timings_ms": {
            "retrieval": _safe_round(stage_timings_ms.get("retrieval")),
            "context_enrichment": _safe_round(
                stage_timings_ms.get("context_enrichment")
            ),
            "sql_context_preparation": _safe_round(
                stage_timings_ms.get("sql_context_preparation")
            ),
            "sql_generation": _safe_round(stage_timings_ms.get("sql_generation")),
            "sql_validation": _safe_round(stage_timings_ms.get("sql_validation")),
            "sql_execution": _safe_round(stage_timings_ms.get("sql_execution")),
            "total": _safe_round(total_elapsed_ms),
        },
        "retrieval": {
            "retrieved_candidate_count": len((sql_context or {}).get("candidates", [])),
            "suggested_candidate_index": suggested_candidate_index,
            "chosen_candidate_index": chosen_candidate_index,
            "candidate_changed_by_model": candidate_changed_by_model,
            "suggested_dataset_name": (sql_context or {}).get("suggested_dataset_name"),
            "chosen_dataset_name": generated_query.get("chosen_dataset_name"),
        },
        "query_mode": {
            "suggested_mode_for_chosen_candidate": suggested_mode,
            "final_mode": final_mode,
            "mode_changed_by_model": mode_changed_by_model,
            "mode_decision": generated_query.get("mode_decision"),
        },
        "openai_decision": {
            "changed_candidate_or_mode": candidate_changed_by_model
            or mode_changed_by_model
        },
        "validation": {
            "is_valid": validation.get("is_valid") if validation else None,
            "violation_count": len(validation.get("violations", [])) if validation else 0,
        },
        "execution": {
            "executed": execution is not None,
            "row_count_returned": execution.get("row_count_returned") if execution else 0,
        },
    }
    return metrics


def append_query_metrics(log_path: Path, metrics: dict) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as file_handle:
        file_handle.write(json.dumps(metrics, ensure_ascii=False) + "\n")


def load_query_metrics(log_path: Path) -> list[dict]:
    if not log_path.exists():
        return []

    records = []
    with log_path.open("r", encoding="utf-8") as file_handle:
        for line in file_handle:
            stripped = line.strip()
            if not stripped:
                continue
            records.append(json.loads(stripped))
    return records


def _average(values: list[float]) -> Optional[float]:
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def summarize_query_metrics(records: list[dict]) -> dict:
    total_queries = len(records)
    status_counts = Counter(record.get("status", "unknown") for record in records)

    candidate_changed_count = sum(
        1
        for record in records
        if record.get("retrieval", {}).get("candidate_changed_by_model") is True
    )
    mode_changed_count = sum(
        1
        for record in records
        if record.get("query_mode", {}).get("mode_changed_by_model") is True
    )
    any_model_change_count = sum(
        1
        for record in records
        if record.get("openai_decision", {}).get("changed_candidate_or_mode") is True
    )
    validation_success_count = sum(
        1
        for record in records
        if record.get("validation", {}).get("is_valid") is True
    )
    execution_success_count = sum(
        1
        for record in records
        if record.get("execution", {}).get("executed") is True
    )

    timing_keys = [
        "retrieval",
        "context_enrichment",
        "sql_context_preparation",
        "sql_generation",
        "sql_validation",
        "sql_execution",
        "total",
    ]
    average_timings_ms = {}
    for key in timing_keys:
        values = []
        for record in records:
            value = record.get("timings_ms", {}).get(key)
            if isinstance(value, (int, float)):
                values.append(float(value))
        average_timings_ms[key] = _average(values)

    final_mode_counts = Counter()
    suggested_mode_counts = Counter()
    mode_transition_counts = Counter()
    for record in records:
        query_mode = record.get("query_mode", {})
        suggested_mode = query_mode.get("suggested_mode_for_chosen_candidate")
        final_mode = query_mode.get("final_mode")
        if suggested_mode:
            suggested_mode_counts[suggested_mode] += 1
        if final_mode:
            final_mode_counts[final_mode] += 1
        if suggested_mode and final_mode:
            mode_transition_counts[f"{suggested_mode} -> {final_mode}"] += 1

    return {
        "total_queries": total_queries,
        "status_counts": dict(status_counts),
        "validation_success_count": validation_success_count,
        "validation_success_rate": _average(
            [100.0 * validation_success_count / total_queries] if total_queries else []
        ),
        "execution_success_count": execution_success_count,
        "execution_success_rate": _average(
            [100.0 * execution_success_count / total_queries] if total_queries else []
        ),
        "candidate_changed_count": candidate_changed_count,
        "candidate_changed_rate": _average(
            [100.0 * candidate_changed_count / total_queries] if total_queries else []
        ),
        "mode_changed_count": mode_changed_count,
        "mode_changed_rate": _average(
            [100.0 * mode_changed_count / total_queries] if total_queries else []
        ),
        "any_model_change_count": any_model_change_count,
        "any_model_change_rate": _average(
            [100.0 * any_model_change_count / total_queries] if total_queries else []
        ),
        "average_timings_ms": average_timings_ms,
        "suggested_mode_counts": dict(suggested_mode_counts),
        "final_mode_counts": dict(final_mode_counts),
        "mode_transition_counts": dict(mode_transition_counts),
    }
