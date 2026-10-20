# RandyllAI

RandyllAI is a Streamlit chat assistant that helps students explore South Korean university information. It retrieves relevant passages from university documents stored in Qdrant and uses a local Ollama model to generate answers with source details.

## How it works

1. Extract text from PDF documents in `data/pdfs/`.
2. Split the extracted text into chunks, create embeddings with `BAAI/bge-m3`, and store them in Qdrant.
3. At question time, retrieve the most relevant chunks and send them as context to Ollama (`gemma3:4b`).
4. Display the answer and retrieved document names and pages in the Streamlit app.

The assistant is instructed to answer from the retrieved documents and cite sources. Verify important admission information against the original university documents.

## Requirements

- Python 3.11
- Docker Desktop
- [Ollama](https://ollama.com/)
- University PDF documents that you have permission to use

## Setup

Run these commands from the project root.

### 1. Create a virtual environment and install packages

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install streamlit requests sentence-transformers qdrant-client PyMuPDF
```

For the OCR example in `backend/test_ocr.py`, install Docling as well:

```powershell
pip install docling
```

### 2. Start Qdrant

```powershell
docker compose up -d qdrant
```

Qdrant's dashboard is available at [http://localhost:6333/dashboard](http://localhost:6333/dashboard).

### 3. Start Ollama and download the model

Make sure Ollama is running, then run:

```powershell
ollama pull gemma3:4b
```

### 4. Add and index university documents

Place PDF files in `data/pdfs/`, then run the extraction and indexing steps from the project root:

```powershell
python backend\extract_pdfs.py
python backend\index_documents.py
```

The extraction script writes `data/extracted.json`. The indexing script creates the `randyll_korea_test` collection in Qdrant. **Running the indexing script again deletes and recreates that collection.**

The text extraction script may skip scanned PDFs that do not contain selectable text. OCR experimentation is in `backend/test_ocr.py`.

### 5. Run the app

```powershell
streamlit run frontend\app.py
```

Open the local URL printed by Streamlit, usually [http://localhost:8501](http://localhost:8501).

## Configuration

The current service and model settings are defined in `backend/rag.py`:

- Qdrant: `http://localhost:6333`
- Ollama generation API: `http://localhost:11434/api/generate`
- Embedding model: `BAAI/bge-m3`
- Ollama model: `gemma3:4b`
- Qdrant collection: `randyll_korea_test`

The app expects Qdrant and Ollama to be reachable at these addresses.

## Troubleshooting

- **Qdrant connection error:** Check that Docker is running and start Qdrant with `docker compose up -d qdrant`.
- **Ollama connection error:** Check that Ollama is running and that `gemma3:4b` is installed.
- **No relevant documents found:** Confirm the PDFs are in `data/pdfs/` and rerun both extraction and indexing.
- **Scanned PDFs produce no text:** Use OCR; the regular extraction script only reads text already present in the PDF.

## Project structure

```text
backend/
  extract_pdfs.py     Extract text from PDFs
  index_documents.py  Chunk, embed, and index extracted text
  rag.py              Retrieval and answer generation
  test_ocr.py         OCR processing example
frontend/
  app.py              Streamlit chat interface
data/
  pdfs/               Input PDF documents (not included)
  extracted.json      Generated extracted text
  ocr_output/         Generated OCR Markdown
docker-compose.yml    Qdrant service configuration
```

## Document use

The university documents used as source material are not included in this repository. Add only documents you are authorized to use or redistribute, and follow their copyright and licensing terms.
