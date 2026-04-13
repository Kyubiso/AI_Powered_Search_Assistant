# 📊 Healthcare Dataset Retrieval System (RAG-based)

## 🧠 Opis projektu

Celem projektu jest stworzenie systemu, który umożliwia użytkownikowi zadawanie pytań dotyczących datasetów z obszaru healthcare i otrzymywanie trafnych odpowiedzi na podstawie lokalnej bazy danych — bez korzystania z internetu.

System wykorzystuje podejście **RAG (Retrieval-Augmented Generation)**:
- wyszukuje najbardziej pasujące datasety przy użyciu embeddingów i vector database,
- generuje odpowiedź wyłącznie na podstawie znalezionych danych,
- eliminuje halucynacje modelu (brak zgadywania).

---

## 🎯 Główne funkcjonalności

- 🔍 Wyszukiwanie datasetów na podstawie zapytań użytkownika
- 📄 Wyświetlanie:
  - nazwy datasetu
  - opisu
  - kolumn
  - linku do źródła
- 📊 Możliwość pobrania konkretnych kolumn lub przykładowych wierszy
- ❌ Brak halucynacji — system odpowiada tylko na podstawie danych lokalnych

---

## 🏗️ Architektura systemu

System składa się z dwóch głównych etapów:

### 1. Ingestion & Indexing (budowanie bazy wiedzy)
- wczytanie datasetów (CSV)
- ekstrakcja metadanych
- generowanie embeddingów
- zapis do vector database

### 2. Query Processing (obsługa zapytań)
- użytkownik wpisuje pytanie
- generowany jest embedding zapytania
- wyszukiwanie podobnych datasetów
- zwrócenie wyników + odpowiedź

---

## 🧩 Komponenty systemu

### 📥 Data Ingestion
- wczytywanie datasetów (CSV)
- ekstrakcja:
  - nazw kolumn
  - liczby rekordów
  - przykładowych wierszy

### 🏷️ Metadata Builder
- tworzenie opisu datasetu:
  - nazwa
  - opis
  - kolumny
  - domena (healthcare)
  - sample data

### 🔢 Embedding Generator
- konwersja tekstu na embeddingi
- model embeddingowy (np. sentence-transformers)

### 🗄️ Vector Database
- przechowywanie:
  - embeddingów
  - metadanych
- umożliwia szybkie wyszukiwanie podobieństwa

### 🔎 Retriever
- przyjmuje zapytanie użytkownika
- wyszukuje top-k podobnych datasetów

### 🧾 Answer Builder
- buduje odpowiedź:
  - lista datasetów
  - dopasowane kolumny
  - przykładowe dane

### 💬 Query Interface
- na start: CLI (konsola)
- opcjonalnie: Streamlit (GUI)

---

## 🔄 Przepływ danych (Data Flow)

1. Dataset (CSV) → ingestion
2. Ekstrakcja metadanych
3. Budowa opisu tekstowego
4. Generowanie embeddingów
5. Zapis do vector DB

Zapytanie:
1. User query
2. Embedding query
3. Similarity search (vector DB)
4. Top-k results
5. Generowanie odpowiedzi

---

## 🧠 RAG (Retrieval-Augmented Generation)

System działa według schematu:

User Query  
↓  
Embedding  
↓  
Vector DB Search  
↓  
Top-K Results  
↓  
LLM / Formatter  
↓  
Final Answer


Model językowy:
- NIE generuje wiedzy samodzielnie
- korzysta tylko z danych znalezionych w bazie

---

## ⚙️ Technologie

### Backend
- Python
- pandas

### Embeddingi
- sentence-transformers (lokalnie)
  lub
- OpenAI embeddings (opcjonalnie)

### Vector Database
- ChromaDB lub FAISS

### Interface
- CLI (na start)
- Streamlit (opcjonalnie)

---

## 📁 Struktura projektu

![schema](schema.png)
<!--project/  
│  
├── data/                # datasety CSV  
├── vector_db/           # baza wektorowa  
│  
├── ingest.py            # wczytywanie danych  
├── build_index.py       # embeddingi + zapis  
├── search.py            # wyszukiwanie  
├── main.py              # CLI  
│  
└── utils/  
    ├── metadata.py  
    └── embeddings.py  
-->
---

## 🚀 Fazy projektu

## 🔹 Faza 1 — MVP (na midterm)

Cel: działający system wyszukiwania

Zakres:
- 5–10 datasetów healthcare
- lokalne CSV
- generowanie metadanych
- embeddingi
- vector DB
- zapytania z konsoli
- zwracanie top-3 datasetów

Efekt:
✔ działający prototyp  
✔ możliwość demonstracji  

---

## 🔹 Faza 2 — Rozszerzenie funkcjonalności

- filtrowanie kolumn
- zwracanie konkretnych danych
- lepsze formatowanie odpowiedzi
- obsługa różnych typów zapytań

---

## 🔹 Faza 3 — Interfejs użytkownika

- Streamlit UI:
  - input field
  - lista wyników
  - podgląd danych

---

## 🔹 Faza 4 — Rozbudowa systemu

- dodawanie nowych datasetów
- automatyczne ingestion
- wyszukiwanie po kolumnach
- ranking datasetów

---

## 🔒 Założenia bezpieczeństwa

- brak dostępu do internetu podczas zapytań
- brak halucynacji
- odpowiedzi tylko na podstawie danych lokalnych
- jawne wskazanie źródła (dataset)

---

## 📌 MVP — definicja

Minimalna wersja projektu, która:
- działa end-to-end
- pokazuje ideę RAG
- umożliwia wyszukiwanie datasetów

Nie zawiera:
- UI webowego
- chmury
- zaawansowanych agentów
- automatycznego pobierania danych

---

## 📅 Plan realizacji (krótki)

1. Pobranie datasetów
2. Wczytanie CSV (pandas)
3. Generowanie metadanych
4. Embeddingi
5. Vector DB
6. CLI search
7. Testy ręczne

---

## 💡 Możliwe rozszerzenia

- integracja z Kaggle API
- dynamiczne dodawanie datasetów
- bardziej zaawansowany agent
- analiza jakości danych
- system rekomendacji datasetów

---

## 🧾 Podsumowanie

Projekt implementuje system wyszukiwania datasetów medycznych oparty na RAG, który:
- działa lokalnie
- jest bezpieczny (no hallucination)
- wykorzystuje nowoczesne podejście AI (embeddingi + vector DB)
- jest skalowalny i możliwy do rozbudowy
