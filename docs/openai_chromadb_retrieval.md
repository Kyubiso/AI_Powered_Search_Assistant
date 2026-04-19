# OpenAI Embeddings and ChromaDB Retrieval

## Purpose

These utilities create the first retrieval layer of the project:

- dataset metadata is embedded with OpenAI embeddings
- vectors are stored in ChromaDB
- user queries are embedded and matched against the stored datasets

Scripts:

- `src/backend/retrieval/generate_embeddings.py`
- `src/backend/retrieval/search_datasets.py`

## Model choice

Current default embedding model:

- `text-embedding-3-small`

Reason:

- lower cost
- good enough for the current small dataset collection
- easy to switch later with `--model`

If you want higher-quality embeddings later, you can switch to:

- `text-embedding-3-large`

## Requirements

Python packages:

- `openai`
- `chromadb`

Environment variable:

- `OPENAI_API_KEY`

Example install:

```bash
pip install openai chromadb
```

Example API key setup:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

## Embedding generation

Script:

- `src/backend/retrieval/generate_embeddings.py`

What it does:

1. reads `metadata/Manifests/datasets_manifest.json`
2. opens each referenced file from `metadata/datasets/`
3. takes `embedding_text`
4. sends it to OpenAI embeddings API
5. stores the vector and basic dataset metadata in ChromaDB

Default behavior:

- skips datasets that already exist in ChromaDB

Optional behavior:

- `--force` rebuilds embeddings
- `--dataset "Dataset Name"` limits processing to selected datasets

Examples:

```bash
python -m src.backend.retrieval.generate_embeddings
python -m src.backend.retrieval.generate_embeddings --force
python -m src.backend.retrieval.generate_embeddings --dataset "Drug-Drug Interactions Dataset" --force
```

## Search

Script:

- `src/backend/retrieval/search_datasets.py`

What it does:

1. embeds the user query with OpenAI
2. queries the ChromaDB collection
3. returns the top matching datasets as JSON

Example:

```bash
python -m src.backend.retrieval.search_datasets "Which dataset contains medication side effects?"
```

## Stored data

The ChromaDB collection stores:

- `id`
- embedding vector
- `embedding_text`
- metadata such as:
  - dataset name
  - file path
  - source
  - domain
  - row count
  - column count

Default local database directory:

- `chroma_db/`

Default collection name:

- `dataset_metadata`

## Learning notes

The retrieval flow is now split into two layers:

1. metadata generation
   - builds clean text descriptions from CSV files and manifest data
2. embedding and search
   - converts those descriptions into vectors and performs similarity search

This separation is important because:

- metadata can be regenerated without touching the vector database
- embeddings can be rebuilt later with a different model
- search stays simple because it only depends on prepared embedding text
