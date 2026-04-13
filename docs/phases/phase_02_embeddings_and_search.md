# Phase 02 Embeddings and Search

## Purpose

This document captures the project state after the first working retrieval layer was completed.

## Phase Outcome

The project now supports semantic dataset retrieval over local healthcare datasets using OpenAI embeddings and ChromaDB.

Working flow:

1. local CSV datasets are stored in `data/`
2. manifest entries describe datasets
3. metadata is generated into `metadata/datasets/`
4. `embedding_text` is embedded with OpenAI
5. vectors are stored in ChromaDB
6. natural language queries retrieve the most relevant datasets

## Completed Work In This Phase

### 1. Metadata generation automation

Script:

- `utilities/generate_dataset_metadata.py`

Current behavior:

- reads `metadata/Manifests/datasets_manifest.json`
- loads CSV files with `pandas`
- creates metadata JSON files in `metadata/datasets/`
- skips already existing metadata by default
- supports `--force`
- supports `--dataset`

### 2. Embedding generation

Script:

- `utilities/generate_embeddings.py`

Current behavior:

- reads metadata files referenced by the manifest
- sends `embedding_text` to OpenAI embeddings API
- stores vectors in local ChromaDB
- skips already embedded datasets by default
- supports `--force`
- supports `--dataset`

Current default model:

- `text-embedding-3-small`

### 3. Vector search

Script:

- `utilities/search_datasets.py`

Current behavior:

- embeds a user query with OpenAI
- searches the ChromaDB collection
- returns ranked dataset matches as JSON

### 4. Documentation

Human-readable usage documentation was added:

- `README.md`
- `docs/usage_guide.md`
- `docs/generate_dataset_metadata.md`
- `docs/openai_chromadb_retrieval.md`

## Validation Performed

The following were confirmed:

- metadata generation works for the three current datasets
- embeddings were successfully generated for all three datasets
- ChromaDB contains three records
- semantic search returns sensible ranking

Example validated query:

- `"Which dataset contains medication side effects and warnings?"`

Expected top result:

- `Drug Labels and Side Effects Dataset`

This behavior was confirmed.

## Current Assets

### Datasets

- `data/Final_Augmented_dataset_Diseases_and_Symptoms.csv`
- `data/db_drug_interactions.csv`
- `data/realistic_drug_labels_side_effects.csv`

### Manifest

- `metadata/Manifests/datasets_manifest.json`

### Generated metadata

- `metadata/datasets/Final_Augmented_dataset_Diseases_and_Symptoms.json`
- `metadata/datasets/db_drug_interactions.json`
- `metadata/datasets/realistic_drug_labels_side_effects.json`

### Retrieval storage

- `chroma_db/`

## Current Conventions

- dataset CSV files must be stored in `data/`
- manifest is the curated source of truth
- metadata files are generated artifacts
- embeddings are generated from `embedding_text`
- ChromaDB is the local vector store for search

## Known Notes

- the side effects dataset description in the manifest says `1,393` records
- the actual CSV contains `1,436` rows
- generated metadata uses the actual CSV row count

## Fallback State

If later work needs a rollback point, this phase means:

- metadata generation is automated
- embeddings generation is implemented and tested
- semantic dataset search is implemented and tested
- usage documentation exists
- the project has a working dataset-level retrieval MVP
