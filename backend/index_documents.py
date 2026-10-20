import json
import uuid

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

COLLECTION = "randyll_korea_test"

embedding_model = SentenceTransformer("BAAI/bge-m3")

client = QdrantClient(url="http://localhost:6333")

with open("data/extracted.json", encoding="utf-8") as f:
    pages = json.load(f)

# Simple character-based chunking for the first test
def split_text(text, size=1800, overlap=200):
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])

        if end == len(text):
            break

        start = end - overlap

    return chunks

records = []

for page in pages:
    for chunk_number, chunk in enumerate(
        split_text(page["text"])
    ):
        records.append({
            "filename": page["filename"],
            "page": page["page"],
            "chunk_number": chunk_number,
            "text": chunk
        })

print(f"Total chunks: {len(records)}")

if not records:
    raise RuntimeError("No text chunks found.")

texts = [record["text"] for record in records]

vectors = embedding_model.encode(
    texts,
    normalize_embeddings=True,
    batch_size=8,
    show_progress_bar=True
)

if client.collection_exists(COLLECTION):
    client.delete_collection(COLLECTION)

client.create_collection(
    collection_name=COLLECTION,
    vectors_config=models.VectorParams(
        size=vectors.shape[1],
        distance=models.Distance.COSINE
    )
)

for start in range(0, len(records), 64):
    points = []

    for i in range(start, min(start + 64, len(records))):
        points.append(
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vectors[i].tolist(),
                payload=records[i]
            )
        )

    client.upsert(
        collection_name=COLLECTION,
        points=points,
        wait=True
    )

print("University documents indexed successfully!")