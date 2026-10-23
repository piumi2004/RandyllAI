# Randyll AI Assistant

Randyll AI is a Retrieval-Augmented Generation (RAG) assistant for Korean universities. It helps students answer questions about admissions, tuition, scholarships, and proof-of-funds requirements by searching a curated knowledge base and grounding answers in university source material.

## Overview

This project combines:

- A Streamlit web app for chatting with the assistant
- A Python backend for semantic retrieval and answer generation
- Qdrant as the vector database for document search
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
pip install streamlit python-dotenv sentence-transformers qdrant-client anthropic google-genai
```

4. Create a `.env` file in the project root with your API settings.

Example:

```env
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=your_anthropic_key
CLAUDE_MODEL=claude-haiku-5-5

GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=models/gemini-3.8-flash
```

If you use Claude, set `LLM_PROVIDER=claude`.
If you use Gemini, set `LLM_PROVIDER=gemini`.

## Run the vector database

This project uses Qdrant for semantic retrieval. Start it with Docker Compose:

```powershell
docker compose up -d
```

This spins up the `qdrant` service defined in `docker-compose.yml`.

## Index the knowledge base

To create or refresh the vector index, run:

```powershell
python backend\index_knowledge.py
```

If you are working from extracted PDF text data instead, you can also run:

```powershell
python backend\index_documents.py
```

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
3. A semantic search queries Qdrant for the most relevant document chunks.
4. The most relevant sources are retrieved and passed to the LLM.
5. The model answers the question while referencing the retrieved material.

This process helps reduce hallucinations and keeps responses grounded in the university data included in the project.

## Data sources

The project stores its knowledge in `data/`, including curated documents and extracted content. The retrieval layer indexes these documents into a Qdrant collection such as:

```text
randyll_korea_knowledge_v2
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

### Missing API key

Check that the required values are present in `.env` and that the selected provider matches the key you configured.

### Empty or weak answers

- Rebuild the vector index after updating the knowledge base.
- Confirm the Qdrant collection exists and contains indexed points.
- Check that the `data/` folder contains valid source documents.

## Notes

This project is primarily a local research and knowledge-assistant setup. It is intended for educational and institutional guidance use, and it depends on external API access and vector search tooling to function correctly.
