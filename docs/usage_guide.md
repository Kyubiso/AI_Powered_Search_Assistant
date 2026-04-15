# Usage Guide

## What this project does

This project helps you search local healthcare datasets by meaning, not only by file name.

Instead of manually opening every CSV file, you:

1. describe datasets in the manifest
2. generate metadata from local CSV files
3. turn metadata into embeddings
4. search datasets with natural language queries
5. import datasets into DuckDB for local SQL querying
6. prepare schema context for the future text-to-SQL step

## Before you start

Make sure:

- dataset CSV files are placed in `data/`
- the manifest points to the correct files
- `OPENAI_API_KEY` is available in the shell
- required packages are installed
- DuckDB database can be built locally from the manifest-listed CSV files

## Full workflow

### 1. Put CSV files in `data/`

Example:

```bash
data/Final_Augmented_dataset_Diseases_and_Symptoms.csv
data/db_drug_interactions.csv
data/realistic_drug_labels_side_effects.csv
```

### 2. Update the manifest

File:

- `metadata/Manifests/datasets_manifest.json`

Each dataset entry should include:

- `file_path`
- `metadata_path`
- `dataset_name`
- `source`
- `created_at`
- `domain`
- `description`

### 3. Generate metadata

Command:

```bash
python utilities/generate_dataset_metadata.py
```

What happens:

- CSV is loaded with `pandas`
- row and column information is extracted
- sample rows are saved
- `description` and `embedding_text` are created
- metadata JSON is written to `metadata/datasets/`

### 4. Generate embeddings

Command:

```bash
source ~/.zshrc
python utilities/generate_embeddings.py
```

What happens:

- each dataset metadata file is opened
- `embedding_text` is sent to OpenAI embeddings API
- vectors are stored in ChromaDB

### 5. Search

Command:

```bash
source ~/.zshrc
python utilities/search_datasets.py "Which dataset contains drug warnings and side effects?"
```

What happens:

- the query is embedded with OpenAI
- ChromaDB finds the nearest stored datasets
- the script returns ranked results as JSON

### 6. Build DuckDB database

Command:

```bash
python utilities/build_duckdb.py
```

What happens:

- the manifest is read again
- CSV files are imported into `storage/healthcare.duckdb`
- one DuckDB table is created per active dataset
- existing tables are skipped by default unless `--force` is used

### 7. Inspect DuckDB schema

Commands:

```bash
python utilities/show_duckdb_schema.py --list-tables
python utilities/show_duckdb_schema.py --dataset "Mental Health Survey"
```

For wide tables, you can also ask for question-based column suggestions:

```bash
python utilities/show_duckdb_schema.py --dataset "Diseases and Symptoms Dataset" --question "Which columns can help find symptoms related to fever and cough?" --top-columns 12
```

What happens:

- DuckDB schema is read from the local database
- table names, column names, and types are returned
- for wide tables, a compact set of relevant columns can be suggested

### 8. Prepare SQL context

Commands:

```bash
python utilities/prepare_sql_context.py "Which diseases have fever and cough?" --dataset "Diseases and Symptoms Dataset" --top-columns 8
python utilities/prepare_sql_context.py "Show all symptoms of influenza" --dataset "Diseases and Symptoms Dataset"
python utilities/prepare_sql_context.py "How many respondents received treatment?" --dataset "Mental Health Survey" --top-columns 8
```

What happens:

- the question is classified into a query mode
- the selected table schema is loaded from DuckDB
- a compact or broad column set is prepared for the future SQL generator

Current query modes:

- `focused_filter`
- `broad_profile`
- `aggregate`

### 9. Generate SQL

Commands:

```bash
python utilities/generate_sql.py "Which diseases have fever and cough?" --dataset "Diseases and Symptoms Dataset" --top-columns 8
python utilities/generate_sql.py "How many respondents received treatment?" --dataset "Mental Health Survey" --top-columns 8
```

What happens:

- prepared SQL context is built or reused
- OpenAI receives the selected table and selected columns
- one candidate read-only `SELECT` query is returned as JSON
- the query is not executed automatically

### 10. Validate SQL

Commands:

```bash
python utilities/validate_sql.py "SELECT diseases FROM diseases_and_symptoms_dataset WHERE fever = 1 AND cough = 1 LIMIT 5" --table diseases_and_symptoms_dataset
```

What happens:

- only `SELECT` queries are allowed
- joins and multi-statement queries are rejected
- DuckDB checks the query with `EXPLAIN` in read-only mode

### 11. Run validated SQL

Commands:

```bash
python utilities/run_sql_query.py "SELECT treatment, COUNT(*) AS respondent_count FROM mental_health_survey GROUP BY treatment LIMIT 5" --table mental_health_survey --limit 5
```

What happens:

- validation runs first
- the query is executed only if validation passes
- DuckDB is opened in read-only mode
- result rows are returned as JSON

### 12. Test SQL manually

Commands:

```bash
python utilities/query_duckdb.py "SHOW TABLES"
python utilities/query_duckdb.py "SELECT * FROM mental_health_survey LIMIT 5"
```

What happens:

- the query is executed against local DuckDB
- rows are returned directly in the terminal

### 13. Run the full pipeline

Commands:

```bash
python utilities/ask_database.py "How many respondents received treatment?"
python utilities/ask_database.py "Which diseases have fever and cough?"
```

What happens:

- semantic retrieval selects the best dataset candidate
- SQL context is prepared for the selected DuckDB table
- OpenAI generates one candidate read-only SQL query
- validation checks the query
- the query is executed only if validation passes
- the full pipeline result is returned as JSON

## How to think about it

You do not generate embeddings every time you search.

Correct workflow:

- metadata: generate when datasets change
- embeddings: generate when metadata changes
- DuckDB: rebuild when CSV contents change
- SQL context: prepare when you want to move from dataset retrieval to row-level querying
- search: run as often as you want

So yes:

- embeddings are usually generated once per dataset version
- DuckDB import is usually generated once per dataset version
- search is run many times afterward

## Common commands

Rebuild metadata for everything:

```bash
python utilities/generate_dataset_metadata.py --force
```

Rebuild metadata for one dataset:

```bash
python utilities/generate_dataset_metadata.py --dataset "Drug-Drug Interactions Dataset" --force
```

Rebuild embeddings for everything:

```bash
source ~/.zshrc
python utilities/generate_embeddings.py --force
```

Rebuild embeddings for one dataset:

```bash
source ~/.zshrc
python utilities/generate_embeddings.py --dataset "Drug Labels and Side Effects Dataset" --force
```

Search examples:

```bash
python utilities/search_datasets.py "Which dataset is about diseases and symptoms?"
python utilities/search_datasets.py "I need a dataset about medication interactions"
python utilities/search_datasets.py "Find a dataset with side effects, dosage and warnings"
```

Build DuckDB:

```bash
python utilities/build_duckdb.py --force
python utilities/build_duckdb.py --dataset "Mental Health Survey" --force
```

Inspect schema:

```bash
python utilities/show_duckdb_schema.py --list-tables
python utilities/show_duckdb_schema.py --dataset "Drug Labels and Side Effects Dataset"
```

Prepare SQL context:

```bash
python utilities/prepare_sql_context.py "Show all symptoms of influenza" --dataset "Diseases and Symptoms Dataset"
python utilities/prepare_sql_context.py "How many respondents received treatment?" --dataset "Mental Health Survey" --top-columns 8
```

Generate SQL:

```bash
python utilities/generate_sql.py "Which diseases have fever and cough?" --dataset "Diseases and Symptoms Dataset" --top-columns 8
```

Validate SQL:

```bash
python utilities/validate_sql.py "SELECT diseases FROM diseases_and_symptoms_dataset WHERE fever = 1 AND cough = 1 LIMIT 5" --table diseases_and_symptoms_dataset
```

Run validated SQL:

```bash
python utilities/run_sql_query.py "SELECT treatment, COUNT(*) AS respondent_count FROM mental_health_survey GROUP BY treatment LIMIT 5" --table mental_health_survey --limit 5
```

Run full pipeline:

```bash
python utilities/ask_database.py "How many respondents received treatment?"
```

## Current limitation

The current system now supports retrieval-to-SQL execution in one command, but it still only allows single-table queries and does not support joins.

The next future step could be:

- better answer formatting
- confidence handling or fallback across top retrieved datasets
- controlled join support with explicit allowed relationships
