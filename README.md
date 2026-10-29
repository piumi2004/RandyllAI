# Randyll AI Assistant

Randyll AI is a Retrieval-Augmented Generation (RAG) assistant for Korean universities. It helps students answer questions about admissions, tuition, scholarships, and proof-of-funds requirements by searching a curated knowledge base and grounding answers in university source material.

## Project improvement guide

See the [project improvement guide](docs/improvement-guide.md) for updates to completed steps and instructions for new improvements. The guide will be updated as work progresses, with clear setup steps and checks you can follow.

For the original and updated knowledge flow, diagrams, taxonomy, and review checklist, read [Organizing the knowledge base by domain](docs/knowledge-domains.md).

The [flagged knowledge review](docs/flagged-knowledge-review.md) gives recommendations and justifications for all 78 flagged files. The approved corrections and remaining held content are tracked in [Applying the flagged-file review](docs/knowledge-review-implementation.md).

For Improvement #2, read the [structured-data implementation review](docs/structured-data-review.md), covering what the interns implemented, what is missing, and the next deliverables.

For Improvement #3, follow the [document ingestion guide](docs/document-ingestion-guide.md): the existing work, missing stages, and instructions for Docling + EasyOCR with Korean/English recognition and an AWS deployment path.

## Overview

This project combines:

- A Streamlit web app for chatting with the assistant
- A Python backend for semantic retrieval and answer generation
- Qdrant as the vector database for document search
- PostgreSQL for structured university, program, tuition, and intake records
- Sentence embeddings via BGE-M3
- LLM support for Claude or Gemini
- University knowledge data stored in the `data/` folder

The assistant is designed to answer questions such as:

- What are the admission requirements at Kyungpook National University?
- What is the tuition fee at Dongseo University?
- What scholarships does Tongmyong University offer?
- What is Jeonbuk's graduate proof-of-funds requirement?

## Project structure

```text
RandyllAI/
├── backend/
│   ├── check_universities.py
│   ├── extract_pdfs.py
│   ├── index_documents.py
│   ├── index_knowledge.py
│   ├── rag.py
│   ├── test_claude.py
│   ├── test_gemini.py
│   ├── test_knowledge.py
│   └── test_ocr.py
├── data/
│   ├── extracted.json
│   ├── ocr_output/
│   ├── pdfs/
│   └── Randyll_Semantic_Knowledge/
├── frontend/
│   └── app.py
├── .env
├── .gitignore
├── docker-compose.yml
├── README.md
└── .streamlit/
```

## Tech stack

- Python
- Streamlit
- Qdrant
- PostgreSQL
- SentenceTransformers
- Anthropic Claude SDK
- Google Generative AI SDK
- Docker Compose

## Prerequisites

Before running the project, make sure you have:

- Python 3.10+ (recommended 3.11+)
- Docker Desktop or Docker Engine
- Access to one of the supported LLM APIs:
  - Anthropic Claude
  - Google Gemini

## Setup

1. Clone the repository.

2. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install the required Python packages:

```powershell
pip install streamlit python-dotenv sentence-transformers qdrant-client anthropic google-genai "psycopg[binary]"
```

4. Create a `.env` file in the project root with your API settings.

Example:

```env
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=your_anthropic_key
CLAUDE_MODEL=claude-haiku-5-5

GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=models/gemini-3.8-flash

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=randyll_ai_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=replace_with_a_strong_local_password
```

If you use Claude, set `LLM_PROVIDER=claude`.
If you use Gemini, set `LLM_PROVIDER=gemini`.

## Embedding model: GPU or CPU

The BGE-M3 embedding model runs on your own machine. It picks the GPU automatically when PyTorch can see one, and falls back to the CPU when it can't. You don't need to change any code. The only difference is **which PyTorch you install**.

Both setups produce the same embeddings, so an index built on a GPU machine works fine on a CPU machine and the other way round. The GPU is just much faster, especially for a full `index_knowledge.py` run.

### If you have an NVIDIA GPU

The plain `pip install` in step 3 pulls in a CPU-only PyTorch on Windows, so swap it for the CUDA build. The main workstation runs `torch 2.14.1+cu130` (CUDA 13.0) on an RTX 5070 Ti.

1. Check your driver is installed and see your GPU:

   ```powershell
   nvidia-smi
   ```

2. In your activated `.venv`, replace PyTorch with the CUDA build:

   ```powershell
   pip uninstall -y torch
   pip install torch --index-url https://download.pytorch.org/whl/cu130
   ```

   If your driver is too old for CUDA 13.0, either update the driver or pick an older CUDA build from the [PyTorch install selector](https://pytorch.org/get-started/locally/). Use the matching `cu1xx` index URL.

3. Confirm the GPU is being used:

   ```powershell
   python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
   python test\test_gpu_embeddings.py
   ```

   You should see `True`, then `Model device: cuda:0` and an embedding shape of `(3, 1024)`. BGE-M3 needs roughly 3 GB of GPU memory.

### If you're on CPU only

There's nothing extra to do. The default install from step 3 works. To check, run:

```powershell
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

You'll see a version without `+cu`, and `False`. That's expected. Expect the first model load and full re-indexing to be noticeably slower, so let `index_knowledge.py` run to the end. Skip `test\test_gpu_embeddings.py`, because it deliberately asks for a GPU and will fail on a CPU-only machine.

If you have an NVIDIA GPU but `torch.cuda.is_available()` prints `False`, you almost certainly have the CPU build of PyTorch. Follow the GPU steps above.

## Run the databases

This project uses Qdrant for semantic retrieval and PostgreSQL for structured records. Set a strong PostgreSQL password in `.env` first. From the project root, start both services:

```powershell
docker compose up -d
```

This starts the `qdrant` and `postgres` services defined in `docker-compose.yml`. Both are accessible only through localhost on the host machine, and their data is stored in Docker volumes.

Follow the [database setup and verification instructions](docs/improvement-guide.md#step-1-set-up-qdrant-and-postgresql) to check the services and handle an existing installation. PostgreSQL starts with an empty application database; the university schema and data must be imported separately before the structured queries can work.

### Basic Docker Compose commands

Run these commands from the project root, where `docker-compose.yml` is located.

```powershell
# Start both databases in the background.
docker compose up -d

# Check whether the services are running.
docker compose ps

# View the latest database logs.
docker compose logs --tail 100 qdrant postgres

# Stop and remove the containers and network, keeping database volumes.
docker compose down

# Start the services again using the saved data.
docker compose up -d
```

To reset both databases completely, use:

```powershell
docker compose down -v
```

**This deletes the Compose volumes, including PostgreSQL records, Qdrant indexes, and Qdrant snapshots.** Use it only when you intend to discard that data. The next `docker compose up -d` creates fresh volumes; you will need to restore or reimport the PostgreSQL schema and data and reindex the Qdrant documents.

### Using PostgreSQL in Docker or a native install

There are two ways to run PostgreSQL here, and the app works with either:

- **Docker container.** This is the default in `docker-compose.yml` and what the main workstation uses. Qdrant and PostgreSQL both run as containers.
- **Native install.** PostgreSQL is installed directly on Windows, which is how some of the team have it set up. Qdrant still runs in Docker.

The Python code doesn't care which one you use. It just connects to whatever `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` and `POSTGRES_PASSWORD` in `.env` point at. So switching is mostly a matter of starting the right services and editing `.env`.

#### Option A: both databases in Docker (default)

```powershell
docker compose up -d
docker compose ps
```

Use the `.env` values shown in the Setup section. The container creates `randyll_ai_db` the first time it starts.

#### Option B: native PostgreSQL, Qdrant in Docker

1. Start only Qdrant:

   ```powershell
   docker compose up -d qdrant
   ```

   Compose still reads the whole file, so keep a `POSTGRES_PASSWORD` line in `.env` even though the container isn't running. Your native password works fine there.

2. Point `.env` at your native server. These are the usual defaults for a Windows install:

   ```env
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=randyll_ai_db
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_native_postgres_password
   ```

3. Create the database if you don't have it yet. Run this with the `psql` from your PostgreSQL install, which is usually in `C:\Program Files\PostgreSQL\<version>\bin`:

   ```powershell
   psql -h localhost -U postgres -c "CREATE DATABASE randyll_ai_db;"
   ```

4. Check the app can connect:

   ```powershell
   python test_postgres.py
   ```

   It needs `psycopg` installed and the application tables in place. See the [improvement guide](docs/improvement-guide.md#step-1-set-up-qdrant-and-postgresql).

#### Don't let them fight over port 5432

A native PostgreSQL usually runs as a Windows service on port 5432, and the container wants the same port. If both are running, `docker compose up -d` will fail with a "port is already allocated" error, or worse, the app will quietly connect to the one you didn't mean.

Pick one of these:

- Stop the native service while you use the container. Find its name with `Get-Service *postgres*`, then run `Stop-Service <name>` from an admin PowerShell.
- Or keep both running and move the container to another port by setting `POSTGRES_PORT=5433` in `.env`. Then the container is on 5433, and the app follows whatever `.env` says.

#### Moving data from native PostgreSQL into the container

Do this if you've been working natively and want to switch to Docker, or want to hand your database to someone who uses Docker.

1. Export from the native server. This writes the file directly, so it's safe in PowerShell:

   ```powershell
   pg_dump -h localhost -p 5432 -U postgres -d randyll_ai_db -Fc -f randyll_ai_db.dump
   ```

2. Start the container on a free port (for example `POSTGRES_PORT=5433` if native is still running), then copy the file in and restore it:

   ```powershell
   docker compose up -d postgres
   docker compose cp randyll_ai_db.dump postgres:/tmp/randyll_ai_db.dump
   docker compose exec postgres pg_restore -U postgres -d randyll_ai_db --no-owner /tmp/randyll_ai_db.dump
   ```

#### Moving data from the container to native PostgreSQL

```powershell
docker compose exec postgres pg_dump -U postgres -d randyll_ai_db -Fc -f /tmp/randyll_ai_db.dump
docker compose cp postgres:/tmp/randyll_ai_db.dump randyll_ai_db.dump
pg_restore -h localhost -p 5432 -U postgres -d randyll_ai_db --no-owner randyll_ai_db.dump
```

A couple of things to watch for:

- **Don't use `>` to save a dump in Windows PowerShell.** It re-encodes the output and corrupts the binary file. Always use `-f`, like the commands above.
- **Versions matter.** The container runs PostgreSQL 18.6. A dump made by a newer `pg_dump` may not restore into an older native server. If you hit that, upgrade the native install, or export as plain SQL (`-Fp`) and fix up any errors by hand.
- **Keep dump files out of Git.** They contain your data. Delete them once the restore works.

## Index the knowledge base

To create or refresh the vector index, run:

```powershell
python backend\index_knowledge.py
```

Run `python backend/index_knowledge.py --audit` first to inspect domain assignments and metadata review flags without loading a model or writing to Qdrant. First run `python backend/review_knowledge.py` to generate the reviewed package. The indexer builds a fresh collection, verifies every ID and payload, then promotes the `randyll_korea_knowledge_reviewed` alias. Complete indexing before starting chat. See the [domain guide](docs/knowledge-domains.md) for migration notes and known limits.

For the separate legacy raw-PDF experiment, you can run:

```powershell
python backend\index_documents.py
```

That legacy script writes `randyll_korea_test`, not the collection used by the current chat application.

## Run the app

Start the Streamlit app:

```powershell
streamlit run frontend\app.py
```

Then open the local URL shown in the terminal, typically:

```text
http://localhost:8501
```

## How the assistant works

1. The user asks a question in the web app.
2. The backend detects whether the question refers to a specific university.
3. Semantic retrieval searches Qdrant, using domain hints alongside broad retrieval and matching candidates to the requested university.
4. The most relevant sources are retrieved and passed to the LLM.
5. The model answers the question while referencing the retrieved material.

This process helps reduce hallucinations and keeps responses grounded in the university data included in the project.

## Data sources

The project stores its knowledge in `data/`, including curated documents and extracted content. The retrieval layer indexes these documents into a Qdrant collection such as:

```text
randyll_korea_knowledge_reviewed
```

The assistant is optimized for South Korean university guidance, especially around:

- admissions
- scholarships
- tuition fees
- proof-of-funds requirements
- degree-level requirements

## Troubleshooting

### Qdrant connection errors

Make sure Docker is running and the container is started:

```powershell
docker compose ps
```

If needed, restart it:

```powershell
docker compose down
docker compose up -d
```

### PostgreSQL connection errors

Check which PostgreSQL you meant to use, Docker or native, and that `.env` points at it. If you have both installed, see [Don't let them fight over port 5432](#dont-let-them-fight-over-port-5432).

### Missing API key

Check that the required values are present in `.env` and that the selected provider matches the key you configured.

### Empty or weak answers

- Rebuild the vector index after updating the knowledge base.
- Confirm the Qdrant collection exists and contains indexed points.
- Check that the `data/` folder contains valid source documents.

## Notes

This project is primarily a local research and knowledge-assistant setup. It is intended for educational and institutional guidance use, and it depends on external API access and vector search tooling to function correctly.
