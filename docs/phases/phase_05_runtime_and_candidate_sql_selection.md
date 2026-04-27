# Phase 05 Runtime And Candidate SQL Selection

## Purpose

This note records the next backend changes after the `src/backend/` restructure.

The goal of this phase was to improve runtime behavior and make the SQL stage more flexible when retrieval returns multiple plausible datasets.

## New Behavior

- `src/backend/pipeline/ask_database.py` now supports both:
  - module execution: `python -m src.backend.pipeline.ask_database "..."`
  - direct script execution: `python src/backend/pipeline/ask_database.py "..."`
- `src/backend/sql/generate_sql.py` now supports two input scenarios:
  - single-context mode for direct SQL-generation testing from one prepared dataset/table context
  - multi-candidate mode for the full retrieval pipeline, where the SQL model sees the top retrieved dataset candidates and may switch from the first candidate to a better-fitting second candidate
- in multi-candidate mode, dataset descriptions are taken from `metadata/datasets/*.json` first and used as extra context for SQL generation

## Runtime Scenarios

The backend now supports these main execution patterns:

- Direct SQL testing:
  - prepare one dataset/table context
  - generate SQL for that single context
  - useful for isolated debugging of text-to-SQL behavior
- Full retrieval-to-SQL pipeline:
  - retrieve top dataset candidates from ChromaDB
  - enrich them with DuckDB schema and metadata descriptions
  - let the SQL model keep or change the initially suggested dataset
  - validate and execute SQL against the chosen table only

This means some backend modules intentionally support both older single-context use and newer pipeline use.

## Files Changed

- `src/backend/pipeline/ask_database.py`
- `src/backend/retrieval/retrieve_dataset_candidates.py`
- `src/backend/sql/generate_sql.py`

## Result

After this phase:

- the SQL model is no longer forced to accept only the first retrieved dataset
- the pipeline can provide two strong candidate datasets instead of one rigid choice
- metadata descriptions are part of the SQL decision context
- direct script execution still works while module-style execution remains the preferred path
