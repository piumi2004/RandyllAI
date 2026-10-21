
import uuid
import time
from pathlib import Path

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models


# ==========================================
# CONFIGURATION
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

KNOWLEDGE_DIR = (
    PROJECT_ROOT / "data" / "Randyll_Semantic_Knowledge"
)

CURATED_DIR = KNOWLEDGE_DIR / "CURATED_FACT_SHEETS"

COLLECTION = "randyll_korea_knowledge_v2"

EMBEDDING_MODEL = "BAAI/bge-m3"

QDRANT_URL = "http://localhost:6333"

BATCH_SIZE = 8
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150

# Prefer manually written fact sheets for these universities.
CURATED_UNIVERSITIES = {
    "Dongseo_University",
    "Jeonbuk_National_University",
    "Kyungpook_National_University",
}


# ==========================================
# TEXT CHUNKING
# ==========================================

def split_text(text):
    """
    Split long files into overlapping chunks.
    Short files remain as one chunk.
    """

    text = text.strip()

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):

        end = min(start + CHUNK_SIZE, len(text))

        # Prefer paragraph or line boundaries.
        if end < len(text):
            boundary = text.rfind("\n\n", start + 400, end)

            if boundary == -1:
                boundary = text.rfind("\n", start + 400, end)

            if boundary != -1:
                end = boundary + 1

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(start + 1, end - CHUNK_OVERLAP)

    return chunks


# ==========================================
# LOAD KNOWLEDGE FILES
# ==========================================

def load_documents():

    if not KNOWLEDGE_DIR.exists():
        raise FileNotFoundError(
            f"Knowledge folder not found: {KNOWLEDGE_DIR}"
        )

    documents = []

    txt_files = sorted(KNOWLEDGE_DIR.rglob("*.txt"))

    print(f"Found {len(txt_files)} TXT files.")

    for path in txt_files:

        relative = path.relative_to(KNOWLEDGE_DIR)

        # Skip general README.
        if path.name.lower() == "readme.txt":
            continue

        parts = relative.parts

        is_curated = parts[0] == "CURATED_FACT_SHEETS"

        if is_curated:

            if len(parts) < 3:
                continue

            university = parts[1]
            degree = "Mixed"

        else:

            university = parts[0]

            # Avoid indexing automatic material for the
            # universities with curated fact sheets.
            if university in CURATED_UNIVERSITIES:
                continue

            degree = (
                parts[1] if len(parts) > 2 else "Mixed"
            )

        topic = path.stem.replace("_", " ")

        text = path.read_text(
            encoding="utf-8",
            errors="replace"
        ).strip()

        if not text:
            continue

        source_name = path.name

        # Prefix each embedding with meaningful metadata.
        # This helps semantic search recognize university
        # and topic even for short fact sheets.
        pieces = split_text(text)

        for chunk_number, chunk in enumerate(pieces, start=1):

            embedding_text = (
                f"University: {university.replace('_', ' ')}\n"
                f"Degree level: {degree}\n"
                f"Topic: {topic}\n\n"
                f"{chunk}"
            )

            documents.append({
                "id": str(uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"{relative.as_posix()}::{chunk_number}"
                )),
                "text": embedding_text,
                "university": university.replace("_", " "),
                "degree": degree,
                "topic": topic,
                "filename": source_name,
                "source_path": relative.as_posix(),
                "chunk_number": chunk_number,
                "curated": is_curated
            })

    return documents


# ==========================================
# MAIN INDEXING PROCESS
# ==========================================

def main():

    start_time = time.perf_counter()

    print("=" * 55)
    print("RANDYLL - CATEGORIZED KNOWLEDGE INDEXING")
    print("=" * 55)

    documents = load_documents()

    if not documents:
        raise RuntimeError("No knowledge documents found.")

    print(f"Total chunks to index: {len(documents)}")

    print("\nLoading BGE-M3...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    qdrant = QdrantClient(
        url=QDRANT_URL,
        timeout=120
    )

    vector_size = model.get_sentence_embedding_dimension()

    if vector_size is None:
        raise RuntimeError("Cannot determine embedding size.")

    # Use a NEW collection; don't delete the old PDF index.
    if not qdrant.collection_exists(COLLECTION):

        qdrant.create_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE
            )
        )

        print(f"Created collection: {COLLECTION}")

    else:
        info = qdrant.get_collection(COLLECTION)
        existing_size = info.config.params.vectors.size

        if existing_size != vector_size:
            raise RuntimeError(
                "Existing collection has a different "
                "vector size. Use a new collection name."
            )

        print(f"Using existing collection: {COLLECTION}")

    total_batches = (
        len(documents) + BATCH_SIZE - 1
    ) // BATCH_SIZE

    for batch_index, batch_start in enumerate(
        range(0, len(documents), BATCH_SIZE),
        start=1
    ):

        batch = documents[
            batch_start:batch_start + BATCH_SIZE
        ]

        texts = [item["text"] for item in batch]

        vectors = model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=BATCH_SIZE
        )

        points = []

        for item, vector in zip(batch, vectors):

            points.append(
                models.PointStruct(
                    id=item["id"],
                    vector=vector.tolist(),
                    payload={
                        "text": item["text"],
                        "university": item["university"],
                        "degree": item["degree"],
                        "topic": item["topic"],
                        "filename": item["filename"],
                        "source_path": item["source_path"],
                        "chunk_number": item["chunk_number"],
                        "curated": item["curated"]
                    }
                )
            )

        qdrant.upsert(
            collection_name=COLLECTION,
            points=points,
            wait=True
        )

        print(
            f"Batch {batch_index}/{total_batches} "
            f"completed - {min(batch_start + len(batch), len(documents))}"
            f"/{len(documents)} chunks",
            flush=True
        )

    count = qdrant.count(
        collection_name=COLLECTION,
        exact=True
    ).count

    print("\n" + "=" * 55)
    print("INDEXING COMPLETED")
    print(f"Collection: {COLLECTION}")
    print(f"Vectors stored: {count}")
    print(
        f"Time: {time.perf_counter() - start_time:.2f}s"
    )
    print("=" * 55)


if __name__ == "__main__":
    main()
