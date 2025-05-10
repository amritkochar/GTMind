
# GTMind — Autonomous Research Agent 🔎

> **From a single query to a structured, source‑linked research report.**  
> Searches the web → cleans articles → extracts insights with GPT‑4o → de‑duplicates & ranks → serves JSON, SQLite, CLI, and a Streamlit UI.

---

## ✨ What’s inside?

| Layer | Module | Tech / Libs | Purpose |
|-------|--------|-------------|---------|
| **Search**      | `core/search.py`      | Serper.dev · `httpx`          | Google‑style search → URLs |
| **Parse**       | `core/parse.py`       | Async `httpx` · `trafilatura` | Download & boilerplate‑strip HTML |
| **Extract**     | `core/extract.py`     | OpenAI GPT‑4o · function‑calling | Pull trends, companies, gaps |
| **Aggregate**   | `core/aggregate.py`   | RapidFuzz · frequency rank    | De‑dupe & merge into a report |
| **Persist**     | `persistence.py`      | SQLite · `sqlmodel`           | `--save-sqlite` for history |
| **Serve**       | `api/run.py`          | FastAPI · Typer CLI           | `/report` JSON · `gtmind` CLI cmd |
| **UI**          | `ui/app.py`           | Streamlit                     | Query box, saved list, two‑column companies |

---

## 🖼 Architecture

```mermaid
flowchart LR
    Q(Query) --> S(Search Service)
    S --> P[Downloader + Trafilatura]
    P --> E[OpenAI Extractor]
    E --> A[Aggregator]
    A --> J[ResearchReport JSON]
    J -->|CLI| C[Typer]
    J -->|SQLite| D[(DB)]
    J -->|HTTP| F[FastAPI]
    J -->|UI| U[Streamlit]
```

---

## 📋 Requirements

- Python 3.10+
- OpenAI API key
- Serper.dev API key (for Google-style search)
- Poetry (for dependency management)

---

## 🚀 Quick Start


### Installation and Setup

Clone the repository and install dependencies:

```bash
git clone https://github.com/amritkochar/GTMind.git && cd GTMind
make install  # poetry deps + tools
```

#### Set Up Environment Variables

Before running the application, ensure you have a `.env` file in the root directory. You can create one by copying the provided `.env.example` file:

```bash
cp .env.example .env
```

Then, open the `.env` file and add your API keys:

```bash
OPENAI_API_KEY="sk-•••"
SEARCH_API_KEY="serp_•••"
```

These keys are required for the application to function properly. Please do not commit these keys to Github.

#### Start the Application

Run the following commands to start the backend and frontend services:

```bash
make serve  # FastAPI on :8000
make ui     # Streamlit on :8501
```

### CLI Example

```bash
poetry run gtmind run "AI in biotechnology" \
    --out biotech.json \
    --save-sqlite my.db
```

### API Example

```
GET http://localhost:8000/report?q=AI+in+retail
```

### UI Example

```
streamlit run src/gtmind/ui/app.py
```

* 🔹 Two‑column company list  
* 🟢 Green‑highlighted whitespace gaps  
* 📚 Sidebar of most‑recent reports (reads SQLite)

---

## 📂 Project Layout

```
src/gtmind/
├─ core/                # search, parse, extract, aggregate
├─ api/                 # FastAPI + Typer CLI
├─ ui/                  # Streamlit front‑end
├─ persistence.py       # SQLite helpers
├─ sample_outputs/      # example JSON reports
└─ tests/               # unit + integration
```

---

## 📂 Sample Outputs

Real JSON examples live in [`sample_outputs/`](sample_outputs):

* `ai_in_retail.json`
* `ai_in_healthcare.json`

---

## 🛣 Future Roadmap

* 🔎 Vector cache of article embeddings for faster re‑runs  
* ✨ RAG enrichment for deeper summaries 
* 🌐 OAuth‑guarded web UI & shareable URLs
* 🤖 Scheduled cron search with email digests
* 🐳 Docker container & CI pipeline

---

## 🤝 Contributing

```bash
make check   # lint (ruff) + type‑check (mypy)
make test    # run pytest
```

Pull requests welcome — please keep tests green! 🎉

---
