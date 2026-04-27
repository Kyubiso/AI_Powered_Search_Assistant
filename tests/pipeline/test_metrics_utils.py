import tempfile
import unittest
from pathlib import Path

from src.backend.pipeline.metrics_utils import (
    append_query_metrics,
    build_query_metrics,
    load_query_metrics,
    summarize_query_metrics,
)


class MetricsUtilsTests(unittest.TestCase):
    def test_build_query_metrics_detects_candidate_and_mode_changes(self):
        sql_context = {
            "suggested_candidate_index": 0,
            "suggested_dataset_name": "Mental Health Survey",
            "candidates": [
                {"candidate_index": 0, "dataset_name": "Mental Health Survey", "query_mode": "aggregate"},
                {"candidate_index": 1, "dataset_name": "Drug Labels", "query_mode": "focused_filter"},
            ],
        }
        generated_payload = {
            "generated_query": {
                "chosen_candidate_index": 1,
                "chosen_dataset_name": "Drug Labels",
                "final_mode": "broad_profile",
                "mode_decision": "Need fuller profile columns.",
            }
        }
        validation = {"is_valid": True, "violations": []}
        execution = {"row_count_returned": 5}

        metrics = build_query_metrics(
            question="Show me the full label for aspirin",
            sql_context=sql_context,
            generated_payload=generated_payload,
            validation=validation,
            execution=execution,
            stage_timings_ms={"retrieval": 10.0, "sql_generation": 30.0},
            total_elapsed_ms=55.0,
            status="executed",
        )

        self.assertTrue(metrics["retrieval"]["candidate_changed_by_model"])
        self.assertTrue(metrics["query_mode"]["mode_changed_by_model"])
        self.assertTrue(metrics["openai_decision"]["changed_candidate_or_mode"])
        self.assertEqual(
            metrics["query_mode"]["suggested_mode_for_chosen_candidate"],
            "focused_filter",
        )
        self.assertEqual(metrics["query_mode"]["final_mode"], "broad_profile")

    def test_append_load_and_summarize_query_metrics(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "query_metrics.jsonl"
            append_query_metrics(
                log_path,
                {
                    "status": "executed",
                    "timings_ms": {"total": 100.0, "sql_generation": 20.0},
                    "retrieval": {"candidate_changed_by_model": True},
                    "query_mode": {
                        "mode_changed_by_model": False,
                        "suggested_mode_for_chosen_candidate": "aggregate",
                        "final_mode": "aggregate",
                    },
                    "openai_decision": {"changed_candidate_or_mode": True},
                    "validation": {"is_valid": True},
                    "execution": {"executed": True},
                },
            )
            append_query_metrics(
                log_path,
                {
                    "status": "validation_failed",
                    "timings_ms": {"total": 200.0, "sql_generation": 40.0},
                    "retrieval": {"candidate_changed_by_model": False},
                    "query_mode": {
                        "mode_changed_by_model": True,
                        "suggested_mode_for_chosen_candidate": "focused_filter",
                        "final_mode": "aggregate",
                    },
                    "openai_decision": {"changed_candidate_or_mode": True},
                    "validation": {"is_valid": False},
                    "execution": {"executed": False},
                },
            )

            records = load_query_metrics(log_path)
            summary = summarize_query_metrics(records)

        self.assertEqual(len(records), 2)
        self.assertEqual(summary["total_queries"], 2)
        self.assertEqual(summary["status_counts"]["executed"], 1)
        self.assertEqual(summary["status_counts"]["validation_failed"], 1)
        self.assertEqual(summary["candidate_changed_count"], 1)
        self.assertEqual(summary["mode_changed_count"], 1)
        self.assertEqual(summary["validation_success_count"], 1)
        self.assertEqual(summary["execution_success_count"], 1)
        self.assertEqual(summary["average_timings_ms"]["total"], 150.0)
        self.assertEqual(summary["mode_transition_counts"]["aggregate -> aggregate"], 1)
        self.assertEqual(
            summary["mode_transition_counts"]["focused_filter -> aggregate"], 1
        )


if __name__ == "__main__":
    unittest.main()
