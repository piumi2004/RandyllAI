"""Load topic files without embedding models or database side effects."""
import csv
import re
import uuid
from collections import Counter, defaultdict
from pathlib import Path

if __package__:
    from .knowledge_domains import TAXONOMY, classify_topic
else:
    from knowledge_domains import TAXONOMY, classify_topic

BASE_DIR = Path(__file__).resolve().parent.parent / "data" / "Randyll_Semantic_Knowledge"
CURATED_UNIVERSITIES = {"Dongseo_University", "Jeonbuk_National_University", "Kyungpook_National_University"}


def resolve_root(base=BASE_DIR):
    candidates = [base, base / "Randyll_Semantic_Knowledge"]
    roots = [p for p in candidates if (p / "KNOWLEDGE_INDEX.csv").is_file()]
    if len(roots) != 1:
        raise ValueError("Expected exactly one knowledge root with KNOWLEDGE_INDEX.csv")
    return roots[0]


def split_text(text, size=1200, overlap=150):
    text = text.strip()
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            boundary = text.rfind("\n\n", start + 400, end)
            if boundary == -1:
                boundary = text.rfind("\n", start + 400, end)
            if boundary != -1:
                end = boundary + 1
        chunk = text[start:end].strip()
        if chunk:
            yield chunk
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)


def load_legacy_documents(base=BASE_DIR):
    root = resolve_root(base)
    with (root / "KNOWLEDGE_INDEX.csv").open(encoding="utf-8-sig", newline="") as handle:
        index = {r["file_path"].replace("\\", "/"): r for r in csv.DictReader(handle)}
    curated_available = {u for u in CURATED_UNIVERSITIES
        if any(p.read_text(encoding="utf-8").strip()
               for p in (root / "CURATED_FACT_SHEETS" / u).glob("*.txt"))}
    files = []
    for path in sorted(root.rglob("*.txt")):
        if path.name.lower() == "readme.txt":
            continue
        relative = path.relative_to(root)
        parts = relative.parts
        curated = parts[0] == "CURATED_FACT_SHEETS"
        if len(parts) < (3 if curated else 4):
            raise ValueError(f"Unexpected knowledge file layout: {relative}")
        university = parts[1] if curated else parts[0]
        if not curated and university in curated_available:
            continue
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        topic, domains, review = classify_topic(path.stem)
        row = index.get(relative.as_posix(), {})
        source_match = re.search(r"^(?:ORIGINAL SOURCE|Source):\s*(.+)$", text, re.MULTILINE | re.IGNORECASE)
        source_reference = source_match.group(1).strip() if source_match else ""
        source = row.get("source_document", "")
        if not source:
            document = re.match(r"(.+?\.(?:pdf|md))\b", source_reference, re.IGNORECASE)
            source = document.group(1) if document else ""
        # Retain OCR Markdown sources as such; do not invent an official PDF link.
        source_key = f"{university}/{source or relative.as_posix()}"
        degree = "Mixed" if curated else parts[1]
        if curated:
            for label in ("Undergraduate", "Graduate", "Doctoral"):
                if re.search(r"(?:^|_)" + label + r"(?:_|$)", path.stem, re.IGNORECASE):
                    degree = label
                    break
        reasons = []
        if review:
            reasons.append("unmapped_or_ambiguous_topic")
        if university.startswith("Unverified_"):
            reasons.append("unverified_university")
        if not source:
            reasons.append("missing_source_document")
        files.append({"text": text, "university": university.replace("_", " "),
            "degree": degree, "topic": topic, "original_topic": path.stem,
            "domains": domains, "taxonomy_version": TAXONOMY["version"],
            "review_required": bool(reasons), "review_reasons": reasons,
            "source_document": source, "source_reference": source_reference,
            "document_id": str(uuid.uuid5(uuid.NAMESPACE_URL, source_key)),
            "filename": path.name, "source_path": relative.as_posix(), "curated": curated})
    document_domains = defaultdict(set)
    for file in files:
        document_domains[file["document_id"]].update(file["domains"])
    documents = []
    for file in files:
        for number, chunk in enumerate(split_text(file["text"]), 1):
            metadata = {k: v for k, v in file.items() if k != "text"}
            documents.append({**metadata,
                "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{file['source_path']}::{number}")),
                "chunk_number": number,
                "document_domains": sorted(document_domains[file["document_id"]]),
                "text": f"University: {file['university']}\nDegree level: {file['degree']}\n"
                        f"Topic: {file['topic']}\nDomains: {', '.join(file['domains'])}\n\n{chunk}"})
    return documents


def load_documents(base=None):
    """Production uses the reviewed snapshot; explicit paths support legacy audits."""
    if base is not None:
        return load_legacy_documents(base)
    import json
    manifest = BASE_DIR.parent / "knowledge_reviewed" / "ALL_RECORDS.jsonl"
    if not manifest.is_file():
        raise RuntimeError("Build the reviewed package: python backend/review_knowledge.py")
    records = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines()]
    return [r for r in records if r["status"] == "active" and r["audience"] == "international"]


def payload(document):
    return {k: v for k, v in document.items() if k != "id"}


def audit(documents):
    files = {d["source_path"]: d for d in documents}
    coverage = Counter(domain for d in files.values() for domain in d["domains"])
    sources = {d["document_id"]: {"university": d["university"],
        "source_document": d["source_document"], "domains": d["document_domains"]}
        for d in documents}
    return {"taxonomy_version": TAXONOMY["version"], "chunks": len(documents),
        "files": len(files), "curated_files": sum(d["curated"] for d in files.values()),
        "universities": dict(Counter(d["university"] for d in files.values())),
        "files_per_domain": {key: coverage[key] for key in TAXONOMY["domains"]},
        "uncovered_domains": [key for key in TAXONOMY["domains"] if not coverage[key]],
        "review_queue": [{"source_path": d["source_path"], "reasons": d["review_reasons"]}
                         for d in files.values() if d["review_required"]],
        "source_documents": sources}
