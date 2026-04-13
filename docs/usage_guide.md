# Usage Guide

## What this project does

This project helps you search local healthcare datasets by meaning, not only by file name.

Instead of manually opening every CSV file, you:

1. describe datasets in the manifest
2. generate metadata from local CSV files
3. turn metadata into embeddings
4. search datasets with natural language queries

## Before you start

Make sure:

- dataset CSV files are placed in `data/`
- the manifest points to the correct files
- `OPENAI_API_KEY` is available in the shell
- required packages are installed

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

## How to think about it

You do not generate embeddings every time you search.

Correct workflow:

- metadata: generate when datasets change
- embeddings: generate when metadata changes
- search: run as often as you want

So yes:

- embeddings are usually generated once per dataset version
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

## Current limitation

The search currently returns ranked dataset matches as JSON.

The next future step could be:

- a more user-friendly answer builder
- column-level retrieval
- sample-data previews in the final response
