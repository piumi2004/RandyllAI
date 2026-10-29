
from collections import Counter
from qdrant_client import QdrantClient

if __package__:
    from .knowledge_domains import COLLECTION
else:
    from knowledge_domains import COLLECTION

client = QdrantClient(
    url="http://localhost:6333",
    timeout=60
)

print("\nChecking Qdrant collection...")

info = client.get_collection(COLLECTION)
print("Stored points:", info.points_count)

universities = Counter()
topics = Counter()
domains = Counter()
review_chunks = 0
sample_files = {}

offset = None

while True:
    points, offset = client.scroll(
        collection_name=COLLECTION,
        limit=100,
        offset=offset,
        with_payload=True,
        with_vectors=False
    )

    for point in points:
        payload = point.payload or {}

        university = payload.get(
            "university", "<MISSING>"
        )

        universities[university] += 1
        topics[payload.get("topic", "<MISSING>")] += 1
        domains.update(payload.get("domains", []))
        review_chunks += bool(payload.get("review_required"))

        if university not in sample_files:
            sample_files[university] = payload.get(
                "source_path", payload.get("filename")
            )

    if offset is None:
        break

print("\n========== UNIVERSITY NAMES ==========")

for name, count in universities.most_common():
    print(f"{name!r}: {count} chunks")
    print(" Example:", sample_files[name])

print("\n========== TOPICS ==========")

for topic, count in topics.most_common(20):
    print(f"{topic!r}: {count} chunks")

print("\n========== DOMAINS ==========")
for domain, count in domains.most_common():
    print(f"{domain}: {count} chunks")
print(f"Chunks requiring metadata review: {review_chunks}")
print("\nDONE")
