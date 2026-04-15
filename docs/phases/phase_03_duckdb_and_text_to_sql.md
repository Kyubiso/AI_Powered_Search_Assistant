# Phase 03 DuckDB and Text-to-SQL

## Purpose

This document defines the next implementation phase after the dataset-level retrieval MVP.

The goal of this phase is to move from:

- finding the most relevant dataset

to:

- retrieving concrete rows, values, and aggregates from the selected dataset using SQL

This phase keeps the project local-first and simple. It does not introduce a server-based database or a complex agent framework.

## Why This Phase Is Next

The current system can already:

- store curated dataset metadata
- generate embeddings for dataset descriptions
- retrieve the most relevant dataset with ChromaDB

What is still missing is the ability to answer questions such as:

- "Show side effects related to nausea"
- "Which drug pairs have severe interactions?"
- "How many respondents reported treatment for mental health?"

These questions require structured querying over the actual dataset contents, not only metadata retrieval.

## Phase Goal

Add a local SQL query layer so the system can:

1. select the best dataset using the existing retrieval pipeline
2. inspect the schema of the selected dataset
3. generate a safe SQL query from the user question
4. execute the query locally
5. return the result together with dataset/source context

## Current Progress

The first part of this phase has already been implemented.

Completed so far:

- DuckDB Python package installed in the project environment
- local DuckDB database file created at `storage/healthcare.duckdb`
- CSV-to-DuckDB import utility implemented
- terminal query utility implemented for direct SQL testing
- retrieval-to-schema bridge implemented for SQL preparation
- DuckDB schema inspection utility implemented
- local DuckDB storage added to `.gitignore`

Current verified imported tables:

- `diseases_and_symptoms_dataset`
- `drug_drug_interactions_dataset`
- `drug_labels_and_side_effects_dataset`
- `mental_health_survey`

Verified behavior:

- datasets listed in the manifest are imported into DuckDB
- existing DuckDB tables are skipped by default
- `--force` rebuilds existing tables
- `--dataset` allows rebuilding a selected dataset only

This means the project now has a working local SQL storage layer, but it does not yet have schema-inspection tooling or text-to-SQL generation.
This means the project now has a working local SQL storage layer and schema access layer, but it does not yet have text-to-SQL generation.

## Chosen Technical Direction

### Database

Use DuckDB as the local analytical database.

Reason:

- no server setup is required
- CSV import is simple
- it works well for local analytical queries
- it fits the project's MVP-first and demonstration-friendly approach

### System Shape

The implementation should follow a simple two-stage pipeline:

1. Retrieval stage
   - existing embedding-based dataset search
   - responsibility: choose the most relevant dataset

2. SQL stage
   - schema-aware text-to-SQL generation
   - SQL execution against DuckDB
   - responsibility: extract the actual answer from the selected dataset

Important:

- this should first be implemented as modules or pipeline stages
- it does not need a multi-agent framework
- the word "agent" can be used later as a conceptual description if needed

## Proposed Scope

### 1. DuckDB database build step

Create a utility that:

- creates a local DuckDB database file
- imports all active CSV datasets from the manifest
- creates one table per dataset
- uses stable table names suitable for SQL generation

Suggested examples:

- `Final_Augmented_dataset_Diseases_and_Symptoms.csv` -> `diseases_and_symptoms`
- `db_drug_interactions.csv` -> `drug_interactions`
- `realistic_drug_labels_side_effects.csv` -> `drug_labels_side_effects`
- `mental_health_survey.csv` -> `mental_health_survey`

### 2. Schema inspection support

Create a small utility layer that can expose:

- available tables
- column names
- column types

This schema information will be required by the SQL generation step.

### 3. Text-to-SQL generation

Create a module that:

- accepts the user question
- receives the chosen dataset schema
- generates an SQL query for that dataset

Rules:

- only `SELECT` queries are allowed
- no schema modification commands
- no write operations
- no guessing about tables that do not exist

### 4. SQL execution

Create a query execution module that:

- validates the generated SQL
- runs it against DuckDB
- returns rows, aggregates, or previews

### 5. Answer formatting

Extend the output so the final answer can include:

- selected dataset name
- SQL query used
- result rows or summary values
- source file / dataset reference

## Proposed Files

The exact structure can still be adjusted, but this phase should likely introduce files such as:

- `utilities/build_duckdb.py`
- `utilities/query_duckdb.py`
- `utilities/retrieve_sql_context.py`
- `utilities/show_duckdb_schema.py`
- `utilities/generate_sql.py`
- `utilities/run_sql_query.py`

If later integrated into an application flow, these responsibilities can move into `src/` modules.

## Expected Flow After This Phase

The intended query flow becomes:

1. user enters a natural language question
2. retrieval module selects the most relevant dataset
3. schema for that dataset is loaded from DuckDB
4. SQL is generated from the question and schema
5. SQL is executed locally
6. final answer is formatted from the query result

## Safety Rules

This phase must preserve the main project constraints:

- local-only query answering
- no hallucinated data
- SQL must only access known local tables
- only read-only queries are allowed
- if the system cannot generate a safe query, it should fail clearly instead of guessing

## Out of Scope For This Phase

This phase should not include:

- a web UI
- server deployment
- database administration tooling
- autonomous multi-agent orchestration
- complex query planning across many datasets at once

## Definition of Done

This phase is complete when:

- all active CSV datasets can be loaded into DuckDB
- the schema can be inspected programmatically
- the system can generate safe `SELECT` queries for at least basic user questions
- SQL queries can be executed locally and return useful results
- retrieval and SQL querying can be connected in one end-to-end flow

## Current Status Against Definition of Done

Already done:

- all active CSV datasets can be loaded into DuckDB
- SQL queries can already be executed manually through a terminal utility
- schema can be inspected programmatically
- retrieval results can be enriched with DuckDB table and schema context

Still missing:

- safe text-to-SQL generation
- SQL validation layer for generated queries
- retrieval plus SQL connected into one end-to-end flow

## Relation to Previous Phases

Phase 01 established:

- local datasets
- manifest structure
- metadata generation

Phase 02 established:

- embeddings generation
- ChromaDB storage
- semantic dataset retrieval

Phase 03 builds on both by adding:

- local SQL storage with DuckDB
- schema-aware text-to-SQL
- row-level and aggregate answer retrieval
