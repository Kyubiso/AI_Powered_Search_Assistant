# Healthcare Dataset Retrieval System (RAG-based)

## Project Description

The goal of the project is to create a system that lets the user ask questions about healthcare datasets and receive relevant answers based on a local database, without using the internet.

The system uses a **RAG (Retrieval-Augmented Generation)** approach:
- it searches for the most relevant datasets using embeddings and a vector database,
- it generates an answer only from the retrieved data,
- it eliminates model hallucinations by avoiding guessing.

---

## Main Features

- Search for datasets based on user queries
- Display:
  - dataset name
  - description
  - columns
  - source link
- Optionally return selected columns or sample rows
- No hallucinations: the system answers only on the basis of local data

---

## System Architecture

The system consists of two main stages:

### 1. Ingestion and Indexing
- load datasets (CSV)
- extract metadata
- generate embeddings
- save data to the vector database

### 2. Query Processing
- the user enters a question
- a query embedding is generated
- similar datasets are searched
- results and the final answer are returned

---

## System Components

### Data Ingestion
- load datasets (CSV)
- extract:
  - column names
  - number of records
  - sample rows

### Metadata Builder
- create a dataset description including:
  - name
  - description
  - columns
  - domain (healthcare)
  - sample data

### Embedding Generator
- convert text to embeddings
- use an embedding model such as `sentence-transformers`

### Vector Database
- store:
  - embeddings
  - metadata
- enable fast similarity search

### Retriever
- accepts a user query
- finds the top-k most similar datasets

### Answer Builder
- builds the response:
  - list of datasets
  - matching columns
  - sample data

### Query Interface
- first version: CLI
- optional later version: Streamlit

---

## Data Flow

1. Dataset (CSV) -> ingestion
2. Metadata extraction
3. Text description building
4. Embedding generation
5. Save to vector DB

Query flow:
1. User query
2. Query embedding
3. Similarity search in vector DB
4. Top-k results
5. Response generation

---

## RAG (Retrieval-Augmented Generation)

The system follows this pattern:

User Query
v
Embedding
v
Vector DB Search
v
Top-K Results
v
LLM / Formatter
v
Final Answer

The language model:
- does not generate knowledge on its own,
- uses only the data found in the database.

---

## Technologies

### Backend
- Python
- pandas

### Embeddings
- `sentence-transformers` (local)
or
- OpenAI embeddings (optional)

### Vector Database
- ChromaDB or FAISS

### Interface
- CLI (first)
- Streamlit (optional)

---

## Project Structure

![schema](/Users/inis/AI_Search_Assistant/AI_Powered_Search_Assistant/DOcs/schema.png)

---

## Project Phases

## Phase 1 - MVP (midterm version)

Goal: a working search system

Scope:
- 5-10 healthcare datasets
- local CSV files
- metadata generation
- embeddings
- vector DB
- console queries
- return top 3 datasets

Outcome:
- working prototype
- ready for demonstration

---

## Phase 2 - Feature Expansion

- column filtering
- returning specific data
- better answer formatting
- support for different query types

---

## Phase 3 - User Interface

- Streamlit UI:
  - input field
  - results list
  - data preview

---

## Phase 4 - System Expansion

- adding new datasets
- automatic ingestion
- column-based search
- dataset ranking

---

## Security Assumptions

- no internet access during queries
- no hallucinations
- answers only from local data
- explicit source indication for each answer (dataset)

---

## MVP Definition

The minimal version of the project should:
- work end to end
- demonstrate the RAG idea
- enable dataset search

It does not include:
- web UI
- cloud services
- advanced agents
- automatic data downloading

---

## Short Implementation Plan

1. Collect datasets
2. Load CSV files with pandas
3. Generate metadata
4. Create embeddings
5. Build vector DB
6. Implement CLI search
7. Run manual tests

---

## Possible Extensions

- Kaggle API integration
- dynamic dataset addition
- more advanced agent
- data quality analysis
- dataset recommendation system

---

## Summary

The project implements a RAG-based healthcare dataset search system that:
- works locally,
- is safe (no hallucinations),
- uses a modern AI approach (embeddings + vector DB),
- is scalable and can be expanded later.
