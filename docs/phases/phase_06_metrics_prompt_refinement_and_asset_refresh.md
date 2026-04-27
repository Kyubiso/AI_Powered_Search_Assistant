# Phase 06 Metrics, Prompt Refinement, And Asset Refresh

## Purpose

This note records the next set of backend and UI changes after the candidate-selection phase.

The goal of this phase was to improve:

- observability of runtime behavior
- visibility of model decisions
- consistency of rebuild/setup scripts
- SQL-generation guidance quality
- use of dataset-specific interpretation rules

This phase also captures several repository-structure decisions and naming disputes that were resolved during implementation.

## Main Outcomes

After this phase:

- each end-to-end query can return lightweight runtime metrics
- each query appends one metrics record to a local metrics log
- aggregated metrics can be summarized from the saved log
- the desktop UI can display aggregated metrics in a separate window
- SQL-generation guidance better distinguishes row filtering from column selection
- dataset `data_interpretation_notes` are now passed directly into the SQL-generation prompt
- embeddings generation has been moved into the rebuild/setup area
- a single refresh script now exists to regenerate metadata, embeddings, and DuckDB assets

## Repository Naming And Structure Decisions

### 1. SQL-context file naming dispute resolved

The earlier names:

- `retrieve_sql_context.py`
- `prepare_sql_context.py`

were considered too similar for humans, even though they served different roles.

Resolved rename:

- `src/backend/retrieval/retrieve_sql_context.py` -> `src/backend/retrieval/retrieve_dataset_candidates.py`
- `src/backend/sql/prepare_sql_context.py` -> `src/backend/sql/prepare_sql_generation_context.py`

Reasoning:

- the retrieval module does not prepare SQL directly; it retrieves dataset candidates and enriches them
- the SQL module does not retrieve datasets; it prepares prompt-ready SQL context for one chosen table

Important implementation detail:

- these renames were intentionally done in a Git-friendly way so Git would detect them as renames rather than unrelated delete/create operations

### 2. Embeddings generation location dispute resolved

There was a structural disagreement about whether embeddings generation belongs in:

- `src/backend/retrieval/`

or

- `src/backend/data/`

Decision:

- keep runtime retrieval logic in `src/backend/retrieval/`
- move embeddings generation into `src/backend/data/`

Resolved move:

- `src/backend/retrieval/generate_embeddings.py` -> `src/backend/data/generate_embeddings.py`

Reasoning:

- `generate_embeddings.py` is a rebuild/setup script, not a live runtime retrieval script
- it belongs conceptually with metadata generation and DuckDB build scripts
- this makes the project structure more human-readable:
  - `data/` = build/rebuild assets
  - `retrieval/` = use retrieval assets

### 3. Module execution vs direct script execution dispute clarified

A runtime error occurred when a rebuild script was executed as:

- `python src/backend/retrieval/generate_embeddings.py --force`

This failed because the backend codebase mostly relies on package imports under `src.backend...`.

Clarified rule:

- backend scripts should be treated as module-style entry points by default
- recommended execution style is:
  - `python -m src.backend....`
- only specific files should support direct script execution if that compatibility is explicitly added

This means the codebase is now intentionally package-first rather than uniformly supporting both invocation styles.

## Metrics Work

### 1. Per-query metrics added to pipeline output

The end-to-end pipeline now produces a `metrics` block for each query in:

- `src/backend/pipeline/ask_database.py`

Added metrics include:

- status
- retrieval timing
- context enrichment timing
- SQL-context preparation timing
- SQL-generation timing
- SQL-validation timing
- SQL-execution timing
- total runtime
- whether the model changed the suggested dataset candidate
- whether the model changed the chosen candidate's suggested mode
- whether the model changed either candidate or mode
- validation result
- execution result
- returned row count

This was introduced so each single run can be inspected without opening separate logs.

### 2. Persistent metrics log added

New module:

- `src/backend/pipeline/metrics_utils.py`

Saved metrics path:

- `storage/metrics/query_metrics.jsonl`

Behavior:

- every `ask_database.py` run appends one JSON record
- the log is stored locally only
- the `storage/` directory is already ignored by Git, so metrics logs do not pollute version control

### 3. Aggregated metrics report added

New reporting entry point:

- `src/backend/pipeline/report_metrics.py`

This summarizes saved query metrics into aggregated values such as:

- total query count
- status counts
- validation success count and rate
- execution success count and rate
- candidate-changed count and rate
- mode-changed count and rate
- any-model-change count and rate
- average timings per stage
- suggested-mode counts
- final-mode counts
- mode-transition counts

This was added to answer project questions like:

- how often does the model change the initial dataset choice?
- how often does the model change the suggested query mode?
- how long does each stage take on average?

### 4. Metrics tests added

New tests:

- `tests/pipeline/test_metrics_utils.py`

These tests do not evaluate OpenAI answer quality.

They validate:

- correct detection of candidate-change and mode-change flags
- correct JSONL append/load behavior
- correct aggregation math for counts, rates, averages, and mode transitions

This resolved the question:

- "What are the tests for?"

Answer:

- they verify metrics computation correctness, not model semantic correctness

## UI Work

### 1. Per-query metrics surfaced in SQL details

File changed:

- `src/frontend/ui.py`

The SQL details panel now also shows lightweight per-query metrics such as:

- status
- total runtime
- retrieval runtime
- SQL-generation runtime
- whether the model changed candidate
- whether the model changed mode

### 2. Aggregated metrics popup added

File changed:

- `src/frontend/ui.py`

New behavior:

- the main window now has a `Show Metrics` button
- clicking it opens a separate window
- the window loads aggregated metrics using the existing reporting command
- the popup includes a `Refresh` button
- if the popup is already open, clicking `Show Metrics` again brings it forward and refreshes it

This gives a non-terminal way to inspect cumulative system behavior.

## SQL Prompt Refinement Work

### 1. Problem observed

A concrete runtime example showed:

- the selected dataset was correct
- the filtered row logic was correct
- but the generated SQL returned `SELECT *` even though the user wanted only `side_effects`

This led to the design dispute:

- should SQL generation focus only on row filtering?
- or should it jointly decide row filtering and returned columns?

Decision:

- SQL generation must consider both row filtering and column projection together

### 2. Prompt refined to discourage over-broad projection

File changed:

- `src/backend/sql/generate_sql.py`

The system and user prompt instructions were refined so the model is now explicitly told to:

- solve both row matching and column selection
- return only requested fields when the question is specific
- avoid `SELECT *` in `focused_filter` unless the user explicitly asks for a full profile, full record, all columns, or all information
- reserve broader projection for non-focused scenarios where that output is actually justified

This change was made to reduce cases where the model chooses safe-but-overbroad SQL.

### 3. Intent of the refinement

The intent was not to ban `SELECT *` completely.

Instead, the intent was to express a sharper behavioral rule:

- `focused_filter` should usually mean narrow projection
- broad projection should be exceptional and justified by the user question

## Data Interpretation Notes Work

### 1. Manifest was updated by another collaborator

The dataset manifest now contains `data_interpretation_notes` for datasets.

Examples of newly introduced rules include:

- symptom columns use meaningful binary values
- drug interaction order does not change meaning
- in the drug-label dataset, `drug_name` contains both the base name and a dose suffix
- in the drug-label dataset, `side_effects` is stored as one comma-separated text field
- in the mental health dataset, some fields are categorical, some lowercase-normalized, and some may be missing

These notes were introduced by another person working on the project and needed to be reviewed carefully before prompt work continued.

### 2. Retrieval and metadata already used the notes

Before prompt refinement, the notes were already being used in:

- `src/backend/data/generate_dataset_metadata.py`
- `src/backend/data/generate_embeddings.py`

This means:

- notes were copied into metadata JSON
- notes were included in `embedding_text`
- notes were stored in Chroma metadata

So the notes already helped dataset retrieval quality.

### 3. SQL-generation gap identified

A gap was found:

- the notes were not being passed strongly enough into the SQL-generation prompt

That meant the model could retrieve the right dataset but still miss guidance such as:

- use `LIKE`-style matching when `drug_name` includes dose
- interpret binary symptom columns correctly
- treat certain columns as categorical instead of numeric

### 4. SQL-generation context now includes the notes

Files changed:

- `src/backend/retrieval/retrieve_dataset_candidates.py`
- `src/backend/pipeline/ask_database.py`
- `src/backend/sql/generate_sql.py`

New behavior:

- retrieval enrichment now includes `data_interpretation_notes`
- pipeline candidate contexts now carry those notes forward
- the SQL prompt now shows the notes to the model explicitly

This was done so dataset-specific semantics influence final SQL generation, not only retrieval.

## Asset Refresh Orchestration

### 1. New unified refresh script added

New file:

- `src/backend/data/refresh_backend_assets.py`

Purpose:

- run metadata refresh
- run embeddings refresh
- run DuckDB refresh
- do so from one command instead of three separate rebuild steps

Supported options include:

- `--force`
- `--dataset`
- `--skip-metadata`
- `--skip-embeddings`
- `--skip-db`

### 2. Rebuild helpers refactored for reuse

To support the unified refresh script cleanly, reusable helper functions were added/refactored in:

- `src/backend/data/generate_dataset_metadata.py`
- `src/backend/data/generate_embeddings.py`
- `src/backend/data/build_duckdb.py`

This avoids shelling out from Python and keeps orchestration inside backend code.

### 3. Rebuild behavior clarified

During this phase, the rebuild behavior was clarified and recorded:

- metadata refresh is needed when manifest descriptions or interpretation notes change
- embeddings refresh is needed when metadata or retrieval-facing text changes
- DuckDB rebuild is needed when CSV contents or table data change
- `build_duckdb --force` drops existing tables and recreates them from CSV
- embeddings `--force` re-upserts vectors but does not wipe the whole Chroma directory from scratch

## Small Maintenance Changes

### 1. `.DS_Store` ignore rule added

File changed:

- `.gitignore`

Reason:

- macOS Finder metadata files were appearing as unwanted untracked files

### 2. Lazy embedding-model import added

File changed:

- `src/backend/retrieval/embedding_model.py`

Reason:

- wrapper commands such as `--help` for the new refresh script should not fail just because the heavy ML stack loads too early

Result:

- the `sentence_transformers` import now happens lazily inside `get_embedding_model()`
- command discovery and lightweight CLI operations work more reliably

## Verification Performed

The following checks were performed during this phase:

- compile checks for backend SQL, pipeline, retrieval, data, and frontend modules
- metrics utility tests via `unittest`
- help/CLI validation for the new refresh script
- Git status checks to confirm rename detection behavior where needed

## Practical Result

After this phase, the project is better prepared for final evaluation and iterative tuning because:

- rebuild/setup operations are grouped more cleanly
- model decisions are more observable
- cumulative behavior can be measured
- the UI can expose cumulative metrics directly
- dataset-specific interpretation rules can shape SQL generation
- prompt behavior is more aligned with the user's actual requested output shape

## Remaining Notes

Even after this refinement, SQL generation is still LLM-driven rather than deterministic.

So this phase improves:

- guidance quality
- observability
- semantic context quality

but does not yet replace the SQL stage with structured query planning or a deterministic SQL builder.
