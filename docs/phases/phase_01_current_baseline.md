# Phase 01 Current Baseline

## Purpose

This document captures the current completed project state so later work can refer back to a stable baseline.

## Current Scope

The project is currently focused on three local healthcare-related CSV datasets stored in the `data/` directory:

1. `Final_Augmented_dataset_Diseases_and_Symptoms.csv`
2. `db_drug_interactions.csv`
3. `realistic_drug_labels_side_effects.csv`

These datasets are the active working set for the current MVP-stage ingestion and metadata preparation.

## Completed Work

### 1. Project understanding

The architecture and ingestion instructions in the `docs/` directory were reviewed:

- `docs/Description_en.md`
- `docs/Data_Ingestion_Prompt.md`

The current system direction is a local RAG workflow for healthcare datasets:

- ingest CSV datasets
- extract structured metadata
- generate embedding-ready text
- prepare for later vector search and retrieval

### 2. Dataset download utility

A utility script was added for direct Kaggle downloads by URL:

- `utilities/download_kaggle_csv.py`

Purpose:

- accept a Kaggle dataset link
- download the dataset archive with Kaggle CLI
- extract CSV files into `data/`

### 3. Manifest structure

A shared manifest file is being used for curated human-authored dataset information:

- `metadata/Manifests/datasets_manifest.json`

This manifest stores source-of-truth dataset information such as:

- file path
- metadata path
- dataset name
- source link
- created date
- domain
- curated description

Rule:

- manifest = human-provided dataset description and source information
- dataset metadata = generated technical description from ingestion

### 4. Generated dataset metadata

Structured metadata has been prepared for the three current datasets:

- `metadata/datasets/Final_Augmented_dataset_Diseases_and_Symptoms.json`
- `metadata/datasets/db_drug_interactions.json`
- `metadata/datasets/realistic_drug_labels_side_effects.json`

Each metadata file contains:

- dataset name
- source
- file path
- row count
- column count
- column names
- sample rows
- domain
- generated description
- embedding text

Metadata generation is now automated through:

- `utilities/generate_dataset_metadata.py`

Current behavior:

- reads the shared manifest
- generates metadata JSON from local CSV files
- skips already existing metadata by default
- supports `--force` to rebuild
- supports `--dataset` to target selected datasets

### 5. Manifest cleanup

The manifest was normalized to represent the three active datasets only.

Completed cleanup:

- removed the placeholder `None` entry
- filled missing `dataset_name`
- filled missing `metadata_path`
- filled missing `domain`
- filled missing `created_at`

## Current Data Notes

### Diseases and Symptoms dataset

- very wide symptom matrix
- 246,945 rows
- 378 columns
- 773 unique disease labels

### Drug-drug interactions dataset

- 191,541 rows
- 3 columns
- pairwise drug interaction records with natural language interaction descriptions

### Drug labels and side effects dataset

- actual CSV row count is 1,436
- manifest description text currently says 1,393 records
- this mismatch should be kept in mind if the manifest text is later revised

## Current Conventions

- raw datasets go in `data/`
- curated dataset descriptions go in `metadata/Manifests/datasets_manifest.json`
- generated ingestion metadata goes in `metadata/datasets/`
- work should remain local-first and avoid depending on external dataset descriptions when curated manifest information already exists

## Fallback State

If later work needs a safe rollback point, this baseline means:

- the three datasets are present locally
- the three metadata JSON files exist
- the shared manifest exists and is populated
- the Kaggle download utility exists
- no ingestion pipeline has yet been fully automated beyond metadata preparation

## Next Prepared Step

The next project layer has been scaffolded but not executed end-to-end yet:

- `utilities/generate_embeddings.py`
- `utilities/search_datasets.py`

Target stack:

- OpenAI `text-embedding-3-small` by default
- ChromaDB persistent local vector store

Execution still depends on:

- installing `openai`, `chromadb`, and `duckdb`
- setting `OPENAI_API_KEY`

## Superseded By

This baseline has now been extended by:

- `docs/phases/phase_02_embeddings_and_search.md`
