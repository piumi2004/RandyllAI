
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

if __package__:
    from .knowledge_domains import COLLECTION
else:
    from knowledge_domains import COLLECTION

model = SentenceTransformer("BAAI/bge-m3")
qdrant = QdrantClient(url="http://localhost:6333")

question = "What is the application fee at Dongseo University?"

query_vector = model.encode(
    question,
    normalize_embeddings=True
).tolist()

results = qdrant.query_points(
    collection_name=COLLECTION,
    query=query_vector,
    limit=5,
    with_payload=True
).points

for i, point in enumerate(results, start=1):
    payload = point.payload or {}

    print(f"\n{'=' * 50}")
    print(f"RESULT {i}")
    print("University:", payload.get("university"))
    print("Degree:", payload.get("degree"))
    print("Topic:", payload.get("topic"))
    print("File:", payload.get("filename"))
    print("Score:", round(point.score, 4))
    print("Content:")
    print(payload.get("text", "")[:1200])
