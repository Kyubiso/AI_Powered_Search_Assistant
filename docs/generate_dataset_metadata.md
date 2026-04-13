# Generate Dataset Metadata

## Purpose

This utility generates structured metadata JSON files from the shared dataset manifest and local CSV files.

Script:

- `utilities/generate_dataset_metadata.py`

Input:

- `metadata/Manifests/datasets_manifest.json`
- local CSV files referenced by each manifest entry

Output:

- JSON metadata files in `metadata/datasets/`

## What the script does

For each selected manifest entry, the script:

1. reads the CSV file with `pandas`
2. extracts row count and column count
3. stores the full list of column names
4. stores a small sample of rows
5. reuses manifest information such as dataset name, domain, source, and curated description
6. creates:
   - `description`
   - `embedding_text`
7. writes the result to the dataset's `metadata_path`

## Current behavior

Default behavior:

- process all manifest entries
- skip metadata files that already exist

Optional behavior:

- `--force` regenerates existing metadata files
- `--dataset "Dataset Name"` limits processing to a chosen dataset

## Usage

Generate metadata only for datasets that do not already have metadata:

```bash
python utilities/generate_dataset_metadata.py
```

Regenerate everything:

```bash
python utilities/generate_dataset_metadata.py --force
```

Regenerate one dataset only:

```bash
python utilities/generate_dataset_metadata.py --dataset "Drug-Drug Interactions Dataset" --force
```

Use a custom number of sample rows:

```bash
python utilities/generate_dataset_metadata.py --sample-rows 5
```

## Notes

- The script depends on correct `file_path` and `metadata_path` values in the manifest.
- The manifest is treated as the curated source of truth.
- Generated metadata is reproducible and can be rebuilt from the manifest and CSV files.
- For very wide datasets, the current sample rows include all columns. This may later be optimized for more compact metadata.
