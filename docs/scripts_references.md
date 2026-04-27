# Scripts Reference

This document summarizes the backend scripts under `src/backend/`.

For each script, it explains:

- purpose
- main arguments and flags
- whether it is part of the main pipeline or mainly for setup/debugging
- what it returns

## Structure

Current backend layout:

- `src/backend/data/`
- `src/backend/retrieval/`
- `src/backend/sql/`
- `src/backend/pipeline/`
- `src/backend/inspection/`

## Main Entry Point

The current end-to-end entry point is:

- `src/backend/pipeline/ask_database.py`

Recommended command:

```bash
python -m src.backend.pipeline.ask_database "How many respondents received treatment?"
```

## Data Scripts

### `src/backend/data/download_kaggle_csv.py`

Purpose:
- download a Kaggle dataset archive and extract CSV files into `data/`

Main arguments:
- positional `url`
- `--data-dir`
- `--force`

Role:
- setup only
- not part of final query answering

Return:
- prints progress and extracted file names

### `src/backend/data/generate_dataset_metadata.py`

Purpose:
- generate metadata JSON files from the manifest and local CSV files

Main arguments:
- `--manifest`
- `--sample-rows`
- `--dataset` (repeatable)
- `--force`

Role:
- data preparation
- not used during live answering

Return:
- prints one line per processed dataset
- writes metadata JSON files under `metadata/datasets/`

### `src/backend/data/build_duckdb.py`

Purpose:
- import manifest-listed CSV files into local DuckDB

Main arguments:
- `--manifest`
- `--db-path`
- `--dataset` (repeatable)
- `--force`

Role:
- backend data preparation
- not used directly during query generation

Return:
- prints import/skip status per dataset
- writes `storage/healthcare.duckdb` by default

## Retrieval Scripts

### `src/backend/retrieval/generate_embeddings.py`

Purpose:
- generate OpenAI embeddings from metadata and store them in ChromaDB

Main arguments:
- `--manifest`
- `--chroma-dir`
- `--collection`
- `--model`
- `--dataset` (repeatable)
- `--force`

Role:
- retrieval preparation

Return:
- prints embed/skip status per dataset

### `src/backend/retrieval/search_datasets.py`

Purpose:
- semantic dataset retrieval from ChromaDB

Main arguments:
- positional `query`
- `--chroma-dir`
- `--collection`
- `--model`
- `--top-k`

Role:
- retrieval-only standalone tool
- mainly useful for debugging retrieval quality

Return:
- prints JSON array of retrieved dataset matches

### `src/backend/retrieval/retrieve_dataset_candidates.py`

Purpose:
- retrieve top-k datasets and enrich them with DuckDB table/schema context

Main arguments:
- positional `query`
- `--manifest`
- `--db-path`
- `--chroma-dir`
- `--collection`
- `--model`
- `--top-k`

Role:
- intermediate retrieval/debug tool
- not the main final entry point anymore

Return:
- prints JSON array of retrieved datasets enriched with:
  - table name
  - schema

## SQL Scripts

### `src/backend/sql/prepare_sql_generation_context.py`

Purpose:
- classify question type and select schema context for SQL generation

Main arguments:
- positional `question`
- `--db-path`
- `--manifest`
- `--table`
- `--dataset`
- `--top-columns`

Role:
- core SQL pipeline step

Return:
- prints JSON with:
  - question
  - query mode
  - table name
  - selected columns

Current query modes:
- `focused_filter`
- `broad_profile`
- `aggregate`
- `broad_aggregate`

### `src/backend/sql/generate_sql.py`

Purpose:
- ask OpenAI for one candidate read-only SQL query

Main arguments:
- positional `question`
- `--context-file`
- `--db-path`
- `--manifest`
- `--table`
- `--dataset`
- `--top-columns`
- `--model`

Role:
- core SQL generation step

Return:
- prints JSON with:
  - question
  - query mode
  - table name
  - generated SQL
  - explanation

### `src/backend/sql/validate_sql.py`

Purpose:
- validate generated SQL before execution

Main arguments:
- positional `query`
- `--sql-file`
- `--generated-file`
- `--db-path`
- `--manifest`
- `--table`
- `--dataset`

Role:
- core safety step

Return:
- prints JSON validation result
- exits non-zero when invalid

Checks include:
- only `SELECT`
- no joins
- no multiple statements
- expected single table
- `EXPLAIN` syntax check in DuckDB

### `src/backend/sql/run_sql_query.py`

Purpose:
- validate and then execute read-only SQL against DuckDB

Main arguments:
- positional `query`
- `--sql-file`
- `--generated-file`
- `--db-path`
- `--manifest`
- `--table`
- `--dataset`
- `--limit`

Role:
- core execution step

Return:
- prints JSON containing:
  - validation result
  - execution result

### `src/backend/sql/sql_context_utils.py`

Purpose:
- shared helper module for SQL context preparation

Role:
- internal module
- not intended as the main user-facing CLI

Provides:
- table resolution
- schema loading
- token scoring
- query classification
- selected-column logic

### `src/backend/sql/sql_validation_utils.py`

Purpose:
- shared helper module for SQL validation

Role:
- internal module
- not intended as the main user-facing CLI

Provides:
- SQL loading
- expected-table resolution
- forbidden keyword checks
- single-table checks
- syntax validation via `EXPLAIN`

## Inspection Scripts

### `src/backend/inspection/show_duckdb_schema.py`

Purpose:
- inspect tables and schema in DuckDB

Main arguments:
- `--db-path`
- `--manifest`
- `--table`
- `--dataset`
- `--list-tables`
- `--question`
- `--top-columns`

Role:
- debugging / manual inspection

Return:
- prints JSON with table schema
- optionally prints suggested columns for a question

### `src/backend/inspection/query_duckdb.py`

Purpose:
- run manual ad hoc SQL queries against DuckDB

Main arguments:
- positional `query`
- `--db-path`
- `--limit`

Role:
- debugging / manual testing

Return:
- prints JSON with columns and rows

## Pipeline Script

### `src/backend/pipeline/ask_database.py`

Purpose:
- full end-to-end backend flow
- retrieve dataset
- prepare SQL context
- generate SQL
- validate SQL
- execute SQL

Main arguments:
- positional `question`
- `--manifest`
- `--db-path`
- `--chroma-dir`
- `--collection`
- `--retrieval-model`
- `--sql-model`
- `--retrieval-top-k`
- `--top-columns`
- `--limit`

Role:
- main user-facing backend CLI

Return:
- prints JSON containing:
  - question
  - retrieved candidates
  - selected dataset
  - SQL context
  - generated SQL
  - validation result
  - execution result

## Suggested Practical Usage

If you only want the main current flow:

1. `python -m src.backend.data.generate_dataset_metadata`
2. `python -m src.backend.retrieval.generate_embeddings`
3. `python -m src.backend.data.build_duckdb`
4. `python -m src.backend.pipeline.ask_database "..."`

If you want detailed debugging, additionally use:

1. `python -m src.backend.retrieval.search_datasets "..."`
2. `python -m src.backend.inspection.show_duckdb_schema ...`
3. `python -m src.backend.sql.prepare_sql_generation_context "..."`
4. `python -m src.backend.sql.generate_sql "..."`
5. `python -m src.backend.sql.validate_sql "..."`
6. `python -m src.backend.sql.run_sql_query "..."`
7. `python -m src.backend.inspection.query_duckdb "..."`
