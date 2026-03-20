# Codex Prompt — Data Preparation (RAG Healthcare Project)

## Task

You are helping me prepare datasets for a RAG-based healthcare project.

I will provide:
- a path to a `.csv` file
- optionally a link to the dataset source (e.g. Kaggle)

Your job is to process the dataset and generate structured metadata that will later be used for embeddings and vector search.

---

## What you need to do

For each dataset:

1. Load the CSV using pandas
2. Extract basic information:
   - dataset name (from file name or link)
   - number of rows
   - number of columns
   - column names
3. Take a small sample of data (first 3–5 rows)
4. Infer basic context:
   - what the dataset is about (based on column names + optional link)
   - domain (always healthcare, but be more specific if possible, e.g. cardiology, epidemiology)
5. Build a clean textual description that will be used for embeddings

---

## Output format

Return a Python dictionary like this:

```python
{
  "dataset_name": "...",
  "source": "...",  # link if provided
  "file_path": "...",
  "num_rows": ...,
  "num_columns": ...,
  "columns": [...],
  "sample_rows": [...],  # list of dicts (few rows)
  "domain": "...",
  "description": "...",  # natural language description
  "embedding_text": "..."  # well-structured text for embedding
}