# SideKick

An AI-powered product intelligence platform for sales teams. Upload internal product documents, track competitors, and get grounded answers and competitive analysis — all powered by Claude.

## What it does

- **Document Q&A** — Upload PDFs, Word docs, spreadsheets, and slide decks. Ask questions and get answers cited directly from your internal knowledge base using hybrid RAG (semantic + BM25 search).
- **Competitive Analysis** — Add competitor URLs, auto-scrape their public websites, and run side-by-side comparisons against your own product docs using Claude.
- **Product Management** — Organise documents and competitors under specific products.
- **Streaming Chat** — Responses stream in real time with source citations.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript + Vite |
| Backend | FastAPI (Python 3.12) |
| AI | Anthropic Claude (Sonnet + Haiku) |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Vector DB | ChromaDB |
| Search | Hybrid BM25 + semantic retrieval |
| Database | PostgreSQL 16 |
| Queue | Redis + ARQ |
| Scraping | Playwright (Chromium headless) |

## Getting started

### Prerequisites

- Docker Desktop
- An Anthropic API key

### 1. Configure environment

Copy the example env and fill in your API key:

```bash
cp .env.example .env
```

Edit `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-...
```

The other defaults work out of the box.

### 2. Start the app

```bash
docker-compose up --build
```

First run takes 10–15 minutes (downloads ~2GB of ML dependencies). Subsequent starts are instant.

### 3. Open the app

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

Register a new account on the signup page to get started.

## Project structure

```
SideKick/
├── backend/
│   ├── agents/
│   │   ├── rag_agent.py          # Document Q&A via Claude
│   │   └── competitive_agent.py  # Competitive analysis via Claude
│   ├── api/                      # FastAPI route handlers
│   ├── db/                       # SQLAlchemy models + migrations
│   ├── pipelines/scraping/       # Playwright-based competitor scraper
│   ├── retrieval/                # Hybrid BM25 + semantic search
│   ├── workers/                  # ARQ background job workers
│   └── main.py
├── frontend/
│   └── src/
│       ├── pages/                # Chat, Documents, Competitive, Products
│       └── components/
├── docker-compose.yml
└── .env
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required. Your Anthropic API key |
| `POSTGRES_USER` | `sidekick` | DB username |
| `POSTGRES_PASSWORD` | `sidekick_pass` | DB password |
| `POSTGRES_DB` | `sidekick_db` | DB name |
| `JWT_SECRET_KEY` | — | Secret for signing JWT tokens |
| `CLAUDE_SONNET_MODEL` | `claude-sonnet-4-6` | Model for analysis |
| `CLAUDE_HAIKU_MODEL` | `claude-haiku-4-5-20251001` | Model for lighter tasks |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer model |

## Supported document formats

PDF, DOCX, XLSX, PPTX, Markdown, plain text
