
import time

import argparse
import json
from datetime import datetime, timezone

if __package__:
    from .knowledge_loader import load_documents, payload, audit, resolve_root
    from .knowledge_domains import COLLECTION
else:
    from knowledge_loader import load_documents, payload, audit, resolve_root
    from knowledge_domains import COLLECTION


# ==========================================
# CONFIGURATION
# ==========================================

EMBEDDING_MODEL = "BAAI/bge-m3"

QDRANT_URL = "http://localhost:6333"

BATCH_SIZE = 8


def comparable_payload(value):
    """PDF coordinates tolerate JSON float round-trips; all evidence stays exact."""
    result = dict(value)
    if 'source_region' in result:
        result['source_region'] = [round(v, 6) for v in result['source_region']]
    return result


def verify_and_promote(qdrant, collection, documents):
    from qdrant_client import models
    if collection == COLLECTION:
        raise ValueError('Verify a physical staging collection, not the live alias')
    expected = {d['id']: comparable_payload(payload(d)) for d in documents}
    actual = {}
    offset = None
    while True:
        points, offset = qdrant.scroll(collection_name=collection, limit=128,
                                       offset=offset, with_payload=True, with_vectors=False)
        actual.update({str(p.id): comparable_payload(p.payload) for p in points})
        if offset is None:
            break
    if len(expected) != len(documents) or actual != expected:
        raise RuntimeError('Snapshot verification failed; live alias was not changed')
    operations = []
    if any(a.alias_name == COLLECTION for a in qdrant.get_aliases().aliases):
        operations.append(models.DeleteAliasOperation(delete_alias=models.DeleteAlias(alias_name=COLLECTION)))
    operations.append(models.CreateAliasOperation(create_alias=models.CreateAlias(
        collection_name=collection, alias_name=COLLECTION)))
    qdrant.update_collection_aliases(change_aliases_operations=operations)

# ==========================================
# MAIN INDEXING PROCESS
# ==========================================

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--audit', action='store_true', help='Report metadata without loading models or writing to Qdrant')
    parser.add_argument('--collection', help='New staging collection name; existing collections are rejected')
    parser.add_argument('--verify-only', metavar='STAGING_COLLECTION', help='Verify a finished staging upload and promote it without re-embedding')
    args = parser.parse_args()
    if args.audit:
        from pathlib import Path
        from collections import Counter
        report = audit(load_documents())
        snapshot = Path(__file__).resolve().parent.parent / 'data/knowledge_reviewed/ALL_RECORDS.jsonl'
        report['snapshot_status_counts'] = dict(Counter(json.loads(line)['status']
            for line in snapshot.read_text(encoding='utf-8').splitlines()))
        report['review_scope'] = 'Active-record audit only. Held originals and pending work are listed in REVIEW_LEDGER.json and docs/knowledge-review-implementation.md.'
        print(json.dumps(report, indent=2))
        return
    if args.verify_only:
        from qdrant_client import QdrantClient
        verify_and_promote(QdrantClient(url=QDRANT_URL, timeout=120), args.verify_only, load_documents())
        print(f'Verified and promoted: {args.verify_only}')
        return
    collection = args.collection or 'randyll_korea_knowledge_v4_' + datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    if collection == COLLECTION:
        raise ValueError('The live alias cannot be used as a staging collection')

    from sentence_transformers import SentenceTransformer
    from qdrant_client import QdrantClient, models
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
    if not qdrant.collection_exists(collection):

        qdrant.create_collection(
            collection_name=collection,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE
            )
        )

        print(f"Created collection: {collection}")

    else:
        raise RuntimeError('Refusing to upsert an existing snapshot. Choose a fresh collection name.')

    for field in ('domains', 'document_domains', 'university', 'topic', 'status', 'audience'):
        qdrant.create_payload_index(collection_name=collection, field_name=field,
                                    field_schema=models.PayloadSchemaType.KEYWORD, wait=True)

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
                    payload=payload(item)
                )
            )

        qdrant.upsert(
            collection_name=collection,
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
        collection_name=collection,
        exact=True
    ).count
    verify_and_promote(qdrant, collection, documents)

    print("\n" + "=" * 55)
    print("INDEXING COMPLETED")
    print(f"Verified collection: {collection}; live alias: {COLLECTION}")
    print(f"Vectors stored: {count}")
    print(
        f"Time: {time.perf_counter() - start_time:.2f}s"
    )
    print("=" * 55)


if __name__ == "__main__":
    main()
