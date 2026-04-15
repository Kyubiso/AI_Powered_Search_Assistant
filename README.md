# AI Powered Search Assistant

Local healthcare dataset retrieval project based on a simple RAG-style workflow:

1. keep datasets locally as CSV files
2. generate structured metadata
3. create embeddings from metadata
4. search datasets semantically with OpenAI embeddings and ChromaDB
5. load datasets into DuckDB for later SQL querying
6. prepare schema context for text-to-SQL generation

## Current Project State

The project now supports:

- local dataset-level retrieval with OpenAI embeddings and ChromaDB
- local DuckDB storage for manifest-listed CSV datasets
- schema inspection and SQL-context preparation for the next text-to-SQL step

Implemented parts:

- curated dataset manifest
- metadata generation from CSV files
- OpenAI embedding generation
- ChromaDB vector storage
- semantic search over datasets
- DuckDB import for local SQL storage
- DuckDB schema inspection
- SQL-context preparation with query-mode selection

## Important Rule

All dataset CSV files must be stored in the `data/` directory.

Examples:

- `data/Final_Augmented_dataset_Diseases_and_Symptoms.csv`
- `data/db_drug_interactions.csv`
- `data/realistic_drug_labels_side_effects.csv`

## Project Structure

- `data/` - raw CSV datasets
- `metadata/Manifests/datasets_manifest.json` - curated dataset manifest
- `metadata/datasets/` - generated metadata JSON files
- `src/backend/data/generate_dataset_metadata.py` - metadata generation script
- `src/backend/retrieval/generate_embeddings.py` - embedding generation script
- `src/backend/retrieval/search_datasets.py` - semantic search script
- `src/backend/data/build_duckdb.py` - import manifest-listed CSV files into DuckDB
- `src/backend/inspection/query_duckdb.py` - run manual SQL queries in DuckDB
- `src/backend/inspection/show_duckdb_schema.py` - inspect DuckDB tables and schema
- `src/backend/sql/prepare_sql_context.py` - prepare compact or broad schema context for later SQL generation
- `src/backend/sql/generate_sql.py` - generate a candidate read-only SQL query with OpenAI
- `src/backend/sql/validate_sql.py` - validate generated SQL before execution
- `src/backend/sql/run_sql_query.py` - validate and execute approved SQL in read-only mode
- `src/backend/pipeline/ask_database.py` - end-to-end flow from retrieval to SQL execution
- `docs/` - project notes and usage documentation

## Setup

### 1. Install dependencies

```bash
pip install pandas openai chromadb duckdb
pip install -r requirements.txt
```

This includes: `pandas`, `openai`, `chromadb`, and `duckdb`.

### 2. Configure OpenAI API key

The project reads the API key from the environment:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

If you store it in `~/.zshrc` or `~/.zsh_secrets`, reload your shell:

```bash
source ~/.zshrc
```

### 3. Prepare datasets

Download the datasets and place their CSV files in `data/`.

The manifest should point to those files:

- `metadata/Manifests/datasets_manifest.json`

## How To Use

### Step 1. Generate metadata

This reads the manifest and CSV files, then writes metadata JSON files to `metadata/datasets/`.
 Use **--force** to recreate all datasets metadata or **--dataset** for one specified dataset

```bash
python -m src.backend.data.generate_dataset_metadata
```

Useful options:

```bash
python -m src.backend.data.generate_dataset_metadata --force
python -m src.backend.data.generate_dataset_metadata --dataset "Drug-Drug Interactions Dataset" --force
```

### Step 2. Generate embeddings

This reads the generated metadata, creates OpenAI embeddings, and stores them in ChromaDB.

```bash
python -m src.backend.retrieval.generate_embeddings
```

Useful options:

```bash
python -m src.backend.retrieval.generate_embeddings --force
python -m src.backend.retrieval.generate_embeddings --dataset "Drug Labels and Side Effects Dataset" --force
```

### Step 3. Search datasets

This embeds your query and searches the ChromaDB collection.

```bash
python -m src.backend.retrieval.search_datasets "Which dataset contains medication side effects and warnings?"
```

More examples:

```bash
python -m src.backend.retrieval.search_datasets "I need a dataset about drug interactions"
python -m src.backend.retrieval.search_datasets "Find a dataset about diseases and symptoms"
```

### Step 4. Build DuckDB database

This reads the manifest and imports all active CSV datasets into `storage/healthcare.duckdb`.

```bash
python -m src.backend.data.build_duckdb
```

Useful options:

```bash
python -m src.backend.data.build_duckdb --force
python -m src.backend.data.build_duckdb --dataset "Mental Health Survey" --force
```

### Step 5. Inspect DuckDB schema

Use this to inspect available tables or one selected dataset schema.

```bash
python -m src.backend.inspection.show_duckdb_schema --list-tables
python -m src.backend.inspection.show_duckdb_schema --dataset "Mental Health Survey"
```

For wide tables, you can also ask for question-based column suggestions:

```bash
python -m src.backend.inspection.show_duckdb_schema --dataset "Diseases and Symptoms Dataset" --question "Which columns can help find symptoms related to fever and cough?" --top-columns 12
```

### Step 6. Prepare SQL context

This prepares the table and selected columns that will later be passed into the SQL-generation step.

```bash
python -m src.backend.sql.prepare_sql_context "Which diseases have fever and cough?" --dataset "Diseases and Symptoms Dataset" --top-columns 8
python -m src.backend.sql.prepare_sql_context "Show all symptoms of influenza" --dataset "Diseases and Symptoms Dataset"
python -m src.backend.sql.prepare_sql_context "How many respondents received treatment?" --dataset "Mental Health Survey" --top-columns 8
```

### Step 7. Generate SQL

This uses OpenAI to generate one candidate `SELECT` query from the prepared SQL context.

```bash
python -m src.backend.sql.generate_sql "Which diseases have fever and cough?" --dataset "Diseases and Symptoms Dataset" --top-columns 8
python -m src.backend.sql.generate_sql "How many respondents received treatment?" --dataset "Mental Health Survey" --top-columns 8
```

### Step 8. Validate SQL

This validates a query deterministically before execution.

```bash
python -m src.backend.sql.validate_sql "SELECT diseases FROM diseases_and_symptoms_dataset WHERE fever = 1 AND cough = 1 LIMIT 5" --table diseases_and_symptoms_dataset
```

### Step 9. Run validated SQL

This validates again and then executes the query in read-only mode.

```bash
python -m src.backend.sql.run_sql_query "SELECT treatment, COUNT(*) AS respondent_count FROM mental_health_survey GROUP BY treatment LIMIT 5" --table mental_health_survey --limit 5
```

### Step 10. Test SQL manually

Use DuckDB directly from the terminal:

```bash
python -m src.backend.inspection.query_duckdb "SHOW TABLES"
python -m src.backend.inspection.query_duckdb "SELECT * FROM mental_health_survey LIMIT 5"
```

### Step 11. Run the end-to-end pipeline

This performs retrieval, SQL-context preparation, SQL generation, validation, and execution in one command.

```bash
python -m src.backend.pipeline.ask_database "How many respondents received treatment?"
python -m src.backend.pipeline.ask_database "Which diseases have fever and cough?"
```

## Recommended Workflow

Use this rule:

- generate metadata when you add or change CSV datasets
- generate embeddings when metadata changes or when you add a new dataset
- rebuild DuckDB when the underlying CSV files change
- use schema/context preparation before text-to-SQL generation
- run search whenever you want to test retrieval

In practice:

- metadata generation is occasional
- embedding generation is occasional
- DuckDB rebuild is occasional
- searching is frequent

## Notes

- embeddings are stored locally in `chroma_db/`
- DuckDB is stored locally in `storage/healthcare.duckdb`
- the default embedding model is `text-embedding-3-small`. That means, that you need your Open AI API key.
- metadata generation skips already existing files by default
- embedding generation skips already embedded datasets by default
- DuckDB import skips already existing tables by default
- SQL context preparation supports `focused_filter`, `broad_profile`, and `aggregate` query modes
- generated SQL is validated separately before execution
- execution utilities always open DuckDB in read-only mode
- the full end-to-end flow is now available through `src/backend/pipeline/ask_database.py`

## Documentation

- [Metadata generation guide](/Users/inis/AI_Search_Assistant/AI_Powered_Search_Assistant/docs/generate_dataset_metadata.md)
- [OpenAI + ChromaDB retrieval guide](/Users/inis/AI_Search_Assistant/AI_Powered_Search_Assistant/docs/openai_chromadb_retrieval.md)
- [Current phase baseline](/Users/inis/AI_Search_Assistant/AI_Powered_Search_Assistant/docs/phases/phase_01_current_baseline.md)
- [DuckDB and text-to-SQL phase](/Users/inis/AI_Search_Assistant/AI_Powered_Search_Assistant/docs/phases/phase_03_duckdb_and_text_to_sql.md)
- [Backend restructure phase](/Users/inis/AI_Search_Assistant/AI_Powered_Search_Assistant/docs/phases/phase_04_backend_restructure.md)
- [Scripts reference](/Users/inis/AI_Search_Assistant/AI_Powered_Search_Assistant/docs/scripts_references.md)
- [Usage guide](/Users/inis/AI_Search_Assistant/AI_Powered_Search_Assistant/docs/usage_guide.md)
