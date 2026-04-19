# Phase 04 Backend Restructure

## Purpose

This note records the backend refactor from the old flat `utilities/` layout into a package-based `src/backend/` structure.

The goal of this phase was structural clarity only:

- group scripts by responsibility
- make imports package-based
- prepare the repository for future UI integration
- update command examples and docs to the new paths

## New Directory Structure

The backend code is now grouped under:

- `src/backend/data/`
- `src/backend/retrieval/`
- `src/backend/sql/`
- `src/backend/pipeline/`
- `src/backend/inspection/`

Package files added:

- `src/__init__.py`
- `src/backend/__init__.py`
- `src/backend/data/__init__.py`
- `src/backend/retrieval/__init__.py`
- `src/backend/sql/__init__.py`
- `src/backend/pipeline/__init__.py`
- `src/backend/inspection/__init__.py`

## Files Moved

### Data

- `utilities/download_kaggle_csv.py` -> `src/backend/data/download_kaggle_csv.py`
- `utilities/generate_dataset_metadata.py` -> `src/backend/data/generate_dataset_metadata.py`
- `utilities/build_duckdb.py` -> `src/backend/data/build_duckdb.py`

### Retrieval

- `utilities/search_datasets.py` -> `src/backend/retrieval/search_datasets.py`
- `utilities/retrieve_sql_context.py` -> `src/backend/retrieval/retrieve_sql_context.py`
- `utilities/generate_embeddings.py` -> `src/backend/retrieval/generate_embeddings.py`

### SQL

- `utilities/prepare_sql_context.py` -> `src/backend/sql/prepare_sql_context.py`
- `utilities/generate_sql.py` -> `src/backend/sql/generate_sql.py`
- `utilities/validate_sql.py` -> `src/backend/sql/validate_sql.py`
- `utilities/run_sql_query.py` -> `src/backend/sql/run_sql_query.py`
- `utilities/sql_context_utils.py` -> `src/backend/sql/sql_context_utils.py`
- `utilities/sql_validation_utils.py` -> `src/backend/sql/sql_validation_utils.py`

### Pipeline

- `utilities/ask_database.py` -> `src/backend/pipeline/ask_database.py`

### Inspection

- `utilities/show_duckdb_schema.py` -> `src/backend/inspection/show_duckdb_schema.py`
- `utilities/query_duckdb.py` -> `src/backend/inspection/query_duckdb.py`

## Code Changes

Main code updates made in this phase:

- local `sys.path`-based imports were replaced by package imports under `src.backend`
- entry points now reference domain modules explicitly
- helper modules remain grouped inside the SQL domain instead of a generic `utilities` or `common` folder

## Documentation Changes

The following documentation files were updated to use the new backend paths and command examples:

- `README.md`
- `docs/usage_guide.md`
- `docs/generate_dataset_metadata.md`
- `docs/openai_chromadb_retrieval.md`

## New Documentation

The script reference remains available in:

- `docs/scripts_references.md`

## Result

After this phase:

- the repository no longer treats backend logic as ad hoc utilities
- the codebase is structured by domain responsibility
- future UI work can target `src/backend/` as the backend API/script layer
- command examples should now use module-style execution, for example:
  - `python -m src.backend.pipeline.ask_database "..."`
