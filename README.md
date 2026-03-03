# Enterprise Document Intelligence Platform

An end-to-end Retrieval-Augmented Generation (RAG) starter repository for enterprise document understanding.

## Overview

This project provides:
- **FastAPI backend** for ingestion, retrieval, and chat-like Q&A.
- **Python document pipeline** for loading documents, chunking, embedding, and indexing.
- **FAISS vector search** to retrieve semantically related document chunks.
- **OpenAI integrations** for embeddings and answer generation.
- **Streamlit dashboard** for uploading files and querying the system.
- **Dockerized deployment** with `Dockerfile` and `docker-compose`.
- **RBAC + token auth** (Admin/User) for protected endpoints.
- **Logging + Sentry hooks** for observability.
- **Pytest suite** with basic unit/API tests.

## Repository Structure

```text
.
├── app
│   ├── main.py
│   ├── api
│   │   └── endpoints.py
│   ├── core
│   │   ├── config.py
│   │   ├── prompt_utils.py
│   │   └── security.py
│   └── services
│       ├── embeddings.py
│       ├── retriever.py
│       └── llm_service.py
├── dashboards
│   └── app.py
├── data
│   └── raw_documents/
├── embeddings
│   └── vector_store/
├── scripts
│   └── evaluate_rag.py
├── tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Architecture (ASCII)

```text
┌───────────────┐      upload/search      ┌──────────────────────────────┐
│   Streamlit   │ ───────────────────────▶ │ FastAPI (auth + API routes) │
└───────┬───────┘                          └─────────────┬────────────────┘
        │                                                │
        │                                  ┌─────────────▼─────────────┐
        │                                  │ Ingestion + Chunking       │
        │                                  │ (txt/pdf loaders)          │
        │                                  └─────────────┬─────────────┘
        │                                                │
        │                                  ┌─────────────▼─────────────┐
        │                                  │ OpenAI Embeddings API      │
        │                                  └─────────────┬─────────────┘
        │                                                │
        │                                  ┌─────────────▼─────────────┐
        │                                  │ FAISS Index + Metadata     │
        │                                  └─────────────┬─────────────┘
        │                                                │
        │                                  ┌─────────────▼─────────────┐
        └─────────────────────────────────▶│ Retrieval + OpenAI Chat LLM│
                                           └────────────────────────────┘
```

## Setup

### 1) Clone and install

```bash
git clone <repo-url>
cd Enterprise-Document-Intelligence-RAG-Platform
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure environment

Create `.env`:

```env
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
DATA_DIR=data/raw_documents
VECTOR_STORE_DIR=embeddings/vector_store
AUTH_SECRET_KEY=change-me
AUTH_ALGORITHM=HS256
SENTRY_DSN=
```

### 3) Run backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: `http://localhost:8000/docs`

### 4) Run Streamlit dashboard

```bash
streamlit run dashboards/app.py
```

## Docker

### Build and run with Compose

```bash
docker compose up --build
```

This starts the FastAPI app at `http://localhost:8000` with mounted data/vector directories.


## Deploying on Render

This repo includes a `render.yaml` Blueprint for one-click API deployment.

1. Push this repository to GitHub.
2. In Render, choose **New +** → **Blueprint** and select your repo.
3. Set required secret env vars (`OPENAI_API_KEY`, optionally `SENTRY_DSN`).
4. Deploy. Render will run:

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

After deploy, open these URLs on your Render domain:
- `/` → API status message
- `/health` → healthcheck
- `/version` → shows deployed commit SHA (`RENDER_GIT_COMMIT`)
- `/docs` → interactive Swagger UI
- `/api/v1/search?query=...` → authenticated search endpoint

### If you still see `{"detail":"Not Found"}` at `/`

That means Render is almost certainly serving an older revision.

1. In Render dashboard, open your service and click **Manual Deploy → Deploy latest commit**.
2. If still stale, use **Clear build cache & deploy**.
3. Confirm startup logs mention the new commit and `Application booted with commit=...`.
4. Open `/version` and verify the commit hash matches your latest GitHub commit.

### If you saw dependency resolution errors

Your previous failure was due to a pin conflict: `langchain==0.3.9` requires `numpy<2`, while the repo pinned `numpy==2.2.0`.
This has been fixed by pinning `numpy==1.26.4`, which is compatible with both `langchain` and `faiss-cpu`.

## Running tests

```bash
pytest -q
```

## Deployment Notes

- Replace demo token issuance (`/auth/token`) with a real identity provider (OIDC/SAML) for production.
- Restrict CORS origins in `app/main.py`.
- Use managed secret storage for API keys and signing keys.
- Persist vector store to durable storage (S3, EFS, or DB-backed vector engine).
- Tune retrieval and reranking for your enterprise corpus and compliance requirements.

## Evaluation Script

Use the included script to compute simple retrieval precision@k and latency metrics:

```bash
python scripts/evaluate_rag.py
```

Results are written to `evaluation_results.csv`.
