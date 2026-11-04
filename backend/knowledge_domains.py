"""Shared, inspectable domain rules. No model loading or database connections."""
import json
import re
from pathlib import Path

TAXONOMY = json.loads(Path(__file__).with_name("domain_taxonomy.json").read_text(encoding="utf-8"))
COLLECTION = "randyll_korea_knowledge_reviewed"
LEGACY_COLLECTION = "randyll_korea_knowledge_v2"
UPLOAD_COLLECTION = "randyll_korea_uploaded_documents"


def search_v2(client, vector, limit, accept, domains):
    """Read the older payload format without changing the stored index.

    V2 predates review metadata. Its use must be explicit through the collection
    name; reviewed collections still require active/international records.
    """
    if domains is not None and not set(domains) <= TAXONOMY["domains"].keys():
        raise ValueError("Unknown domain selection")
    results = []
    offset = 0
    batch_size = max(limit, 64)
    while len(results) < limit:
        points = client.query_points(collection_name=LEGACY_COLLECTION, query=vector,
            limit=batch_size, offset=offset, with_payload=True).points
        for point in points:
            payload = dict(point.payload or {})
            if (
                payload.get("status", "active") != "active"
                or payload.get("is_active", True) is False
                or payload.get("audience", "international") != "international"
            ):
                continue
            parts = str(payload.get("source_path", "")).replace("\\", "/").split("/")
            if parts[0] == "Randyll_Semantic_Knowledge":
                parts = parts[1:]
            if len(parts) >= 4 and parts[0] != "CURATED_FACT_SHEETS":
                payload["university"] = parts[0].replace("_", " ")
                payload["degree"] = parts[1].replace("_", " ")
            elif len(parts) >= 3 and parts[0] == "CURATED_FACT_SHEETS":
                payload["university"] = parts[1].replace("_", " ")
                payload["degree"] = "Mixed"
                for label in ("Undergraduate", "Graduate", "Doctoral"):
                    if label.lower() in Path(parts[-1]).stem.lower().split("_"):
                        payload["degree"] = label
                        break
            text = str(payload.get("text", ""))
            if text.startswith("University: Randyll Semantic Knowledge\n") and "\n\n" in text:
                payload["text"] = text.split("\n\n", 1)[1]
            if domains:
                stored_domains = payload.get("domains")
                if stored_domains:
                    point_domains = set(stored_domains)
                else:
                    topic = str(payload.get("topic", "")).replace(" ", "_")
                    point_domains = set(classify_topic(topic)[1])
                if not set(domains) & point_domains:
                    continue
            point.payload = payload
            if accept(point):
                results.append(point)
                if len(results) == limit:
                    break
        if len(points) < batch_size:
            break
        offset += len(points)
    return results


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


def _source_copy_key(point):
    payload = point.payload or {}
    source_name = str(
        payload.get("source_document") or payload.get("filename") or ""
    ).replace("\\", "/").rsplit("/", 1)[-1]
    match = re.match(r"^(.*?)(?:\s*\((\d+)\))?(\.[^.]+)?$", source_name)
    if not match or not match.group(1):
        return None
    identity = f"{match.group(1)}{match.group(3) or ''}".casefold()
    copy_number = int(match.group(2) or 1)
    institution = str(
        payload.get("university_id") or payload.get("university") or ""
    ).casefold().strip()
    degree = str(
        payload.get("degree_level") or payload.get("degree") or ""
    ).casefold().strip()
    return (identity, institution, degree), copy_number


def _keep_latest_source_copies(points):
    active_points = [
        point
        for point in points
        if (point.payload or {}).get("is_active", True) is not False
    ]
    latest = {}
    for point in active_points:
        key = _source_copy_key(point)
        if key is not None:
            latest[key[0]] = max(latest.get(key[0], 0), key[1])
    return [
        point for point in active_points
        if (
            (key := _source_copy_key(point)) is None
            or key[1] == latest[key[0]]
        )
    ]


def domain_filter(domains):
    from qdrant_client import models
    if not set(domains) <= TAXONOMY["domains"].keys():
        raise ValueError("Unknown domain selection")
    conditions = [models.FieldCondition(key="status", match=models.MatchValue(value="active")),
                  models.FieldCondition(key="audience", match=models.MatchValue(value="international"))]
    if domains:
        conditions.append(models.FieldCondition(key="domains", match=models.MatchAny(any=list(domains))))
    return models.Filter(must=conditions)


def search_with_domains(client, collection, vector, question, limit, accept=None,
                        domains=None, additional_collections=()):
    """Explicit selections are strict; inferred hints retain a broad fallback pool.

    Apply institution acceptance before deciding whether a focused result exists.
    Merge by vector score so an inferred keyword never excludes stronger evidence.
    Upload collections use the same eligibility metadata and domain filters.
    """
    institution_accept = accept or (lambda point: True)
    if domains is not None and not set(domains) <= TAXONOMY["domains"].keys():
        raise ValueError("Unknown domain selection")

    def eligible(point):
        payload = point.payload or {}
        return (payload.get("status") == "active"
                and payload.get("is_active", True) is not False
                and payload.get("audience") == "international"
                and institution_accept(point))

    def base_accept(point):
        if collection == LEGACY_COLLECTION:
            payload = point.payload or {}
            return (
                payload.get("status", "active") == "active"
                and payload.get("is_active", True) is not False
                and payload.get("audience", "international") == "international"
                and institution_accept(point)
            )
        return eligible(point)

    selected = list(domains) if domains is not None else infer_domains(question)
    retrieval_limit = max(limit, 64)
    if collection == LEGACY_COLLECTION:
        primary = search_v2(
            client, vector, retrieval_limit, base_accept, domains
        )
    else:
        focused = []
        if selected:
            focused = client.query_points(collection_name=collection, query=vector,
                query_filter=domain_filter(selected), limit=retrieval_limit,
                with_payload=True).points
        if domains is not None and selected:
            primary = [point for point in focused if base_accept(point)]
        else:
            broad = client.query_points(collection_name=collection, query=vector,
                query_filter=domain_filter([]), limit=retrieval_limit,
                with_payload=True).points
            primary = [point for point in broad + focused if base_accept(point)]

    candidates = list(primary)
    for extra_collection in additional_collections:
        if extra_collection == collection or not client.collection_exists(extra_collection):
            continue
        focused = []
        if selected:
            focused = client.query_points(collection_name=extra_collection, query=vector,
                query_filter=domain_filter(selected), limit=retrieval_limit,
                with_payload=True).points
        if domains is not None and selected:
            candidates.extend(point for point in focused if eligible(point))
        else:
            broad = client.query_points(collection_name=extra_collection, query=vector,
                query_filter=domain_filter([]), limit=retrieval_limit,
                with_payload=True).points
            candidates.extend(point for point in broad + focused if eligible(point))

    merged = {str(point.id): point for point in candidates}
    latest = _keep_latest_source_copies(merged.values())
    return sorted(latest, key=lambda point: point.score, reverse=True)[:limit]
