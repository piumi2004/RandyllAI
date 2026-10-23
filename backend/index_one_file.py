
import sys
import time

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

import index_knowledge as idx


def main():
    if len(sys.argv) != 2:
        print(
            'Usage: python backend/index_one_file.py '
            '"Woosong_University/Graduate/'
            'Masters_Programs_Spring_2027.txt"'
        )
        return

    relative_path = sys.argv[1].replace("\\", "/").lstrip("/")
    full_path = idx.KNOWLEDGE_DIR / relative_path

    if not full_path.is_file():
        print(f"ERROR: File not found: {full_path}")
        return

    start = time.perf_counter()

    print("=" * 55)
    print("RANDYLL - SINGLE FILE INDEXING")
    print("=" * 55)
    print("Target:", relative_path)

    # Reuse the original chunking and metadata logic.
    # Loading the document list does not generate embeddings.
    all_documents = idx.load_documents()

    documents = [
        doc for doc in all_documents
        if doc["source_path"] == relative_path
    ]

    if not documents:
        print(
            "ERROR: No chunks generated for this file. "
            "Check the directory structure and curated-file rules."
        )
        return

    print(f"Chunks to upload: {len(documents)}")

    # Never delete or recreate the collection here.
    qdrant = QdrantClient(
        url=idx.QDRANT_URL,
        timeout=120
    )

    if not qdrant.collection_exists(idx.COLLECTION):
        print(
            f"ERROR: Collection '{idx.COLLECTION}' "
            "does not exist. Aborting without changes."
        )
        return

    print("Loading BGE-M3...")
    model = SentenceTransformer(idx.EMBEDDING_MODEL)

    vector_size = model.get_sentence_embedding_dimension()
    info = qdrant.get_collection(idx.COLLECTION)

    existing_size = info.config.params.vectors.size

    if vector_size != existing_size:
        raise RuntimeError(
            "Embedding dimension mismatch. "
            "Existing Qdrant collection was not modified."
        )

    for start_index in range(
        0,
        len(documents),
        idx.BATCH_SIZE
    ):
        batch = documents[
            start_index:start_index + idx.BATCH_SIZE
        ]

        vectors = model.encode(
            [doc["text"] for doc in batch],
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=idx.BATCH_SIZE
        )

        points = []

        for doc, vector in zip(batch, vectors):
            points.append(
                models.PointStruct(
                    id=doc["id"],
                    vector=vector.tolist(),
                    payload={
                        "text": doc["text"],
                        "university": doc["university"],
                        "degree": doc["degree"],
                        "topic": doc["topic"],
                        "filename": doc["filename"],
                        "source_path": doc["source_path"],
                        "chunk_number": doc["chunk_number"],
                        "curated": doc["curated"]
                    }
                )
            )

        qdrant.upsert(
            collection_name=idx.COLLECTION,
            points=points,
            wait=True
        )

        print(
            f"Uploaded {start_index + len(batch)}"
            f"/{len(documents)} chunks"
        )

    total = qdrant.count(
        collection_name=idx.COLLECTION,
        exact=True
    ).count

    print("\nINDEXING COMPLETED")
    print("File:", relative_path)
    print("Chunks processed:", len(documents))
    print("Total collection points:", total)
    print(
        f"Time: {time.perf_counter() - start:.2f}s"
    )
    print("Existing unrelated points were preserved.")


if __name__ == "__main__":
    main()
