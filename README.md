# AI Powered Search Assistant

Local healthcare dataset retrieval project based on a simple RAG-style workflow:

1. keep datasets locally as CSV files
2. generate structured metadata
3. create embeddings from metadata
4. search datasets semantically with OpenAI embeddings and ChromaDB

## Current Project State

The current MVP works on local dataset-level retrieval.

Implemented parts:

- curated dataset manifest
- metadata generation from CSV files
- OpenAI embedding generation
- ChromaDB vector storage
- semantic search over datasets

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
- `docs/` - project notes and usage documentation

## Setup

### 1. Install dependencies

```bash
pip install pandas openai chromadb
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

## Recommended Workflow

Use this rule:

- generate metadata when you add or change CSV datasets
- generate embeddings when metadata changes or when you add a new dataset
- run search whenever you want to test retrieval

In practice:

- metadata generation is occasional
- embedding generation is occasional
- searching is frequent

## Notes

- embeddings are stored locally in `chroma_db/`
- the default embedding model is `text-embedding-3-small`. That means, that you need your Open AI API key.
- metadata generation skips already existing files by default
- embedding generation skips already embedded datasets by default

## Documentation

- [Metadata generation guide](/Users/inis/AI_Search_Assistant/AI_Powered_Search_Assistant/docs/generate_dataset_metadata.md)
- [OpenAI + ChromaDB retrieval guide](/Users/inis/AI_Search_Assistant/AI_Powered_Search_Assistant/docs/openai_chromadb_retrieval.md)
- [Current phase baseline](/Users/inis/AI_Search_Assistant/AI_Powered_Search_Assistant/docs/phases/phase_01_current_baseline.md)
- [Usage guide](/Users/inis/AI_Search_Assistant/AI_Powered_Search_Assistant/docs/usage_guide.md)
