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
- `utilities/generate_dataset_metadata.py` - metadata generation script
- `utilities/generate_embeddings.py` - embedding generation script
- `utilities/search_datasets.py` - semantic search script
- `utilities/build_duckdb.py` - import manifest-listed CSV files into DuckDB
- `utilities/query_duckdb.py` - run manual SQL queries in DuckDB
- `utilities/show_duckdb_schema.py` - inspect DuckDB tables and schema
- `utilities/prepare_sql_context.py` - prepare compact or broad schema context for later SQL generation
- `docs/` - project notes and usage documentation

## Setup

### 1. Install dependencies

```bash
pip install pandas openai chromadb duckdb
```

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
python utilities/generate_dataset_metadata.py
```

Useful options:

```bash
python utilities/generate_dataset_metadata.py --force
python utilities/generate_dataset_metadata.py --dataset "Drug-Drug Interactions Dataset" --force
```

### Step 2. Generate embeddings

This reads the generated metadata, creates OpenAI embeddings, and stores them in ChromaDB.

```bash
python utilities/generate_embeddings.py
```

Useful options:

```bash
python utilities/generate_embeddings.py --force
python utilities/generate_embeddings.py --dataset "Drug Labels and Side Effects Dataset" --force
```

### Step 3. Search datasets

This embeds your query and searches the ChromaDB collection.

```bash
python utilities/search_datasets.py "Which dataset contains medication side effects and warnings?"
```

More examples:

```bash
python utilities/search_datasets.py "I need a dataset about drug interactions"
python utilities/search_datasets.py "Find a dataset about diseases and symptoms"
```

### Step 4. Build DuckDB database

This reads the manifest and imports all active CSV datasets into `storage/healthcare.duckdb`.

```bash
python utilities/build_duckdb.py
```

Useful options:

```bash
python utilities/build_duckdb.py --force
python utilities/build_duckdb.py --dataset "Mental Health Survey" --force
```

### Step 5. Inspect DuckDB schema

Use this to inspect available tables or one selected dataset schema.

```bash
python utilities/show_duckdb_schema.py --list-tables
python utilities/show_duckdb_schema.py --dataset "Mental Health Survey"
```

For wide tables, you can also ask for question-based column suggestions:

```bash
python utilities/show_duckdb_schema.py --dataset "Diseases and Symptoms Dataset" --question "Which columns can help find symptoms related to fever and cough?" --top-columns 12
```

### Step 6. Prepare SQL context

This prepares the table and selected columns that will later be passed into the SQL-generation step.

```bash
python utilities/prepare_sql_context.py "Which diseases have fever and cough?" --dataset "Diseases and Symptoms Dataset" --top-columns 8
python utilities/prepare_sql_context.py "Show all symptoms of influenza" --dataset "Diseases and Symptoms Dataset"
python utilities/prepare_sql_context.py "How many respondents received treatment?" --dataset "Mental Health Survey" --top-columns 8
```

### Step 7. Test SQL manually

Use DuckDB directly from the terminal:

```bash
python utilities/query_duckdb.py "SHOW TABLES"
python utilities/query_duckdb.py "SELECT * FROM mental_health_survey LIMIT 5"
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

## Documentation

- [Metadata generation guide](/Users/inis/AI_Search_Assistant/AI_Powered_Search_Assistant/docs/generate_dataset_metadata.md)
- [OpenAI + ChromaDB retrieval guide](/Users/inis/AI_Search_Assistant/AI_Powered_Search_Assistant/docs/openai_chromadb_retrieval.md)
- [Current phase baseline](/Users/inis/AI_Search_Assistant/AI_Powered_Search_Assistant/docs/phases/phase_01_current_baseline.md)
- [DuckDB and text-to-SQL phase](/Users/inis/AI_Search_Assistant/AI_Powered_Search_Assistant/docs/phases/phase_03_duckdb_and_text_to_sql.md)
- [Usage guide](/Users/inis/AI_Search_Assistant/AI_Powered_Search_Assistant/docs/usage_guide.md)
