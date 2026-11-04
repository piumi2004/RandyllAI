


"""Read legacy v2 records without treating missing metadata as review approval."""
from qdrant_client import models

from backend.knowledge_domains import classify_topic


def search_legacy_collection(client, collection, vector, question, limit,
                             accept=None, domains=None):
    points = client.query_points(
        collection_name=collection,
        query=vector,
        query_filter=models.Filter(must_not=[
            models.FieldCondition(key="status", match=models.MatchAny(
                any=["held", "excluded", "inactive"])),
            models.FieldCondition(key="audience", match=models.MatchAny(
                any=["domestic", "unresolved"])),
            models.FieldCondition(key="review_required", match=models.MatchValue(value=True)),
        ]),
        limit=max(limit, 60),
        with_payload=True,
    ).points
    results = []
    for point in points:
        payload = point.payload or {}
        if accept is not None and not accept(point):
            continue
        if domains:
            _, inferred, _ = classify_topic(payload.get("topic", ""))
            if not set(domains).intersection(inferred):
                continue
        results.append(point)
    return results[:limit]
