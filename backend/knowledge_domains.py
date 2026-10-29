"""Shared, inspectable domain rules. No model loading or database connections."""
import json
import re
from pathlib import Path

TAXONOMY = json.loads(Path(__file__).with_name("domain_taxonomy.json").read_text(encoding="utf-8"))
COLLECTION = "randyll_korea_knowledge_reviewed"


def classify_topic(stem):
    original = re.sub(r"^\d+[_ ]+", "", stem).replace(" ", "_")
    topic = TAXONOMY["aliases"].get(original, original)
    domains = TAXONOMY["topics"].get(topic, [])
    if not set(domains) <= TAXONOMY["domains"].keys():
        raise ValueError(f"Invalid domain mapping for {topic}")
    return topic, sorted(domains), not bool(domains)


def infer_domains(question):
    """Conservative English hints; unsupported wording falls back to broad search."""
    return sorted(domain for domain, terms in TAXONOMY["query_terms"].items()
                  if any(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", question.lower())
                         for term in terms))


def domain_filter(domains):
    from qdrant_client import models
    if not set(domains) <= TAXONOMY["domains"].keys():
        raise ValueError("Unknown domain selection")
    conditions = [models.FieldCondition(key="status", match=models.MatchValue(value="active")),
                  models.FieldCondition(key="audience", match=models.MatchValue(value="international"))]
    if domains:
        conditions.append(models.FieldCondition(key="domains", match=models.MatchAny(any=list(domains))))
    return models.Filter(must=conditions)


def search_with_domains(client, collection, vector, question, limit, accept=None, domains=None):
    """Explicit selections are strict; inferred hints retain a broad fallback pool.

    Apply institution acceptance before deciding whether a focused result exists.
    Merge by vector score so an inferred keyword never excludes stronger evidence.
    """
    institution_accept = accept or (lambda point: True)
    def accept(point):
        payload = point.payload or {}
        return (payload.get("status") == "active" and payload.get("audience") == "international"
                and institution_accept(point))
    selected = list(domains) if domains is not None else infer_domains(question)
    focused = []
    if selected:
        focused = client.query_points(collection_name=collection, query=vector,
            query_filter=domain_filter(selected), limit=limit, with_payload=True).points
    if domains is not None and selected:
        return [point for point in focused if accept(point)][:limit]
    broad = client.query_points(collection_name=collection, query=vector,
        query_filter=domain_filter([]), limit=limit, with_payload=True).points
    merged = {str(point.id): point for point in broad + focused if accept(point)}
    return sorted(merged.values(), key=lambda point: point.score, reverse=True)[:limit]
