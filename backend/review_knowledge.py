"""Rebuild a traceable review snapshot. Never edit the supplied source package.

Run with Python + PyMuPDF. Extraction is deliberately allowlisted: unresolved
sections remain held, rather than being relabeled and silently published.
"""
import csv
import hashlib
import json
import re
import uuid
from collections import Counter, defaultdict
from pathlib import Path

if __package__:
    from .knowledge_loader import BASE_DIR, load_legacy_documents, resolve_root
    from .knowledge_domains import classify_topic, TAXONOMY
else:
    from knowledge_loader import BASE_DIR, load_legacy_documents, resolve_root
    from knowledge_domains import classify_topic, TAXONOMY

PROJECT = Path(__file__).resolve().parent.parent
OUTPUT = PROJECT / "data/knowledge_reviewed"
IDENTITIES = {
    "Unverified_2027_1_en_pdf": ("Yeungnam University College", "Undergraduate"),
    "Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf": ("Gachon University", "Undergraduate"),
    "Unverified_graduate_pdf": ("Kongju National University", "Graduate"),
    "Unverified_undergraduate_pdf": ("Kongju National University", "Undergraduate"),
    "Korean_Language_Program": ("Ajou University", "Non-degree Korean language"),
}
AUDIENCE_HOLDS = {"KIT", "Kunjang_University_College", "Woosuk_University"}
SUPERSEDED_FILES = {
    "Hannam_University/Undergraduate/Hannam_University_Bachelor_s/Documents_Verification.txt",
}


def review_items():
    text = (PROJECT / "docs/flagged-knowledge-review.md").read_text(encoding="utf-8")
    items = []
    for block in re.split(r"(?=#### R\d{3} -)", text)[1:]:
        items.append({"review_id": re.search(r"#### (R\d{3})", block)[1],
                      "original_path": re.search(r"Current path: `([^`]+)`", block)[1],
                      "recommendation": re.search(r"\*\*Proposed action:\*\* (.+)", block)[1],
                      "justification": re.search(r"\*\*Justification:\*\* (.+)", block)[1]})
    if len(items) != 78:
        raise ValueError("Expected the 78 approved review entries")
    return items


def expand_merged_cells(table):
    """Fill only cells covered by a real merged rectangle, never forward-fill."""
    rows = table.extract()
    rectangles = [(box, rows[i][j]) for i, row in enumerate(table.rows)
                  for j, box in enumerate(row.cells) if box and rows[i][j] is not None]
    for i, row in enumerate(table.rows):
        present = [box for box in row.cells if box]
        if not present:
            continue
        y = min(box[1] for box in present) + 0.5
        for j, value in enumerate(rows[i]):
            if value is not None:
                continue
            column = [r.cells[j] for r in table.rows if r.cells[j]]
            x = min(box[0] for box in column) + 0.5
            covering = [value for box, value in rectangles
                        if box[0] <= x < box[2] and box[1] <= y < box[3]]
            if len(set(covering)) == 1:
                rows[i][j] = covering[0]
    return [[re.sub(r"\s+", " ", cell or "").strip() for cell in row] for row in rows]


def build():
    import pymupdf
    root = resolve_root()
    pinned = json.loads(Path(__file__).with_name("knowledge_review_source_hashes.json").read_text(encoding="utf-8"))
    for relative, expected in pinned.items():
        path = PROJECT / "data" / relative if relative.startswith("pdfs/") else root / relative
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Source changed since review: {relative}. Review extraction boundaries before updating its pinned hash.")
    items = review_items()
    by_path = {item["original_path"]: item for item in items}
    legacy = load_legacy_documents()
    source_paths = {d["source_path"]: d for d in legacy}
    records = []
    source_info = {}
    hashes = {}
    for path, d in source_paths.items():
        group = path.split("/")[0]
        university, degree = IDENTITIES.get(group, (d["university"], d["degree"]))
        source_info[d["source_document"]] = (university, degree)
        hashes[path] = hashlib.sha256((root / path).read_bytes()).hexdigest()
    for d in legacy:
        d = dict(d)
        group = d["source_path"].split("/")[0]
        original_university, original_degree = d["university"], d["degree"]
        d["university"], d["degree"] = IDENTITIES.get(group, (original_university, original_degree))
        d["text"] = d["text"].replace(f"University: {original_university}\n", f"University: {d['university']}\n", 1)
        d["text"] = d["text"].replace(f"Degree level: {original_degree}\n", f"Degree level: {d['degree']}\n", 1)
        d["original_path"] = d["source_path"]
        d["status"], d["audience"] = "active", "international"
        d["review_level"] = "baseline_not_fact_checked"
        d["review_reason"] = "Existing content outside this flagged-file review"
        if group in AUDIENCE_HOLDS:
            d.update(status="held", audience="unresolved", review_reason="Applicant route and machine translation require verification; source retained")
        elif group.startswith("Unverified_") or d["source_path"] in by_path or d["source_path"] in SUPERSEDED_FILES:
            d.update(status="held", review_reason="Original extraction superseded where a checked section exists; remaining content awaits reconstruction")
        if d["source_path"] in by_path:
            d["review_id"] = by_path[d["source_path"]]["review_id"]
        if d["status"] == "held":
            d["review_required"] = True
        d["source_path"] = f"{d['university'].replace(' ', '_')}/{d['degree'].replace(' ', '_')}/{Path(d['source_path']).parent.name}/{Path(d['source_path']).name}"
        d["document_id"] = str(uuid.uuid5(uuid.NAMESPACE_URL, d["university"] + "/" + d["source_document"]))
        d["id"] = str(uuid.uuid5(uuid.NAMESPACE_URL, "reviewed/baseline/" + d["id"]))
        records.append(d)

    plans = json.loads((Path(__file__).with_name("knowledge_review_sections.json")).read_text(encoding="utf-8"))
    for plan in plans:
        source = plan["source"]
        if source == "YEUNGNAM":
            source = next(s for s in source_info if s.startswith("2027_1"))
        pdf_path = PROJECT / "data/pdfs" / source
        hashes["pdfs/" + source] = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
        university, degree = source_info[source]
        with pymupdf.open(pdf_path) as pdf:
            page = pdf[plan["page"] - 1]
            x0, y0, x1, y1 = plan.get("region", [0, .04, 1, .95])
            clip = pymupdf.Rect(x0 * page.rect.width, y0 * page.rect.height,
                                x1 * page.rect.width, y1 * page.rect.height)
            text = page.get_text("text", clip=clip, sort=True).strip()
            if "prepend" in plan:
                previous_page, start, end = plan["prepend"]
                previous = pdf[previous_page - 1]
                text = previous.get_text("text", clip=pymupdf.Rect(0, start * previous.rect.height,
                    previous.rect.width, end * previous.rect.height), sort=True).strip() + "\n" + text
            if "checked_text" in plan:
                text = plan["checked_text"]
            if "checked_rows" in plan:
                # For damaged table geometry, use the row transcription checked
                # against the rendered, hash-pinned source. Never flatten it again.
                headers = plan["headers"]
                rows = plan["checked_rows"]
                if not rows or any(len(row) != len(headers) for row in rows):
                    raise ValueError(f"Invalid checked table: {source} p{plan['page']}")
                passages = [plan.get("table_notes", "") + "\n" +
                            "\n".join(f"{h}: {v}" for h, v in zip(headers, row)) for row in rows]
            elif "table" in plan:
                table = page.find_tables().tables[plan["table"]]
                rows = expand_merged_cells(table)
                header_count = plan.get("header_rows", 1)
                headers = plan.get("headers", rows[0])
                if len(headers) != table.col_count or not all(headers):
                    raise ValueError(f"Missing table headings: {source} p{plan['page']}")
                # Full source scope and notes accompany every row. Remove table words
                # from that context so flattened values cannot contradict the rows.
                words = page.get_text("words", clip=clip, sort=True)
                boxes = [pymupdf.Rect(t.bbox) for t in page.find_tables().tables]
                context = " ".join(w[4] for w in words if not any(pymupdf.Rect(w[:4]).intersects(b) for b in boxes))
                passages = [context + "\n" + "\n".join(f"{h}: {v}" for h, v in zip(headers, row))
                            for row in rows[header_count:]]
            else:
                passages = [text]
            for i, passage in enumerate(passages, 1):
                topic, domains, ambiguous = classify_topic(plan["topic"])
                if ambiguous or not passage.strip():
                    raise ValueError(f"Empty or unmapped section: {plan}")
                section = "checked" if "checked_rows" in plan else plan.get('table', 'text')
                key = f"{source}/{plan['page']}/{topic}/{section}/{i}"
                path = f"{university.replace(' ', '_')}/{degree.replace(' ', '_')}/Reviewed/{topic}_p{plan['page']}_{section}.txt"
                records.append({"id": str(uuid.uuid5(uuid.NAMESPACE_URL, "reviewed/section/" + key)),
                    "text": f"University: {university}\nDegree level: {degree}\nTopic: {topic}\nSource: {source}, physical PDF page {plan['page']}\nScope: {plan['scope']}\n\n{passage}",
                    "university": university, "degree": degree, "topic": topic, "original_topic": topic,
                    "domains": domains, "taxonomy_version": TAXONOMY["version"], "status": "active",
                    "audience": "international", "review_level": "local_source_section_checked",
                    "review_required": False, "review_reasons": [], "review_reason": plan["scope"],
                    "source_document": source, "page": plan["page"], "source_region": list(clip),
                    "source_reference": f"{source}, physical PDF page {plan['page']}" +
                        (f"; continuation from page {plan['prepend'][0]}" if "prepend" in plan else ""),
                    "source_path": path, "filename": Path(path).name, "original_path": None,
                    "document_id": str(uuid.uuid5(uuid.NAMESPACE_URL, university + "/" + source)),
                    "curated": True, "chunk_number": i})
    domains = defaultdict(set)
    for d in records:
        if d["status"] == "active":
            domains[d["document_id"]].update(d["domains"])
    for d in records:
        d["document_domains"] = sorted(domains[d["document_id"]])
    if len({d['id'] for d in records}) != len(records):
        raise ValueError("Duplicate record IDs")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "ALL_RECORDS.jsonl").write_text("".join(json.dumps(d, ensure_ascii=False) + "\n" for d in records), encoding="utf-8")
    grouped = defaultdict(list)
    for d in records:
        grouped[d["source_path"]].append(d)
    with (OUTPUT / "KNOWLEDGE_INDEX.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["file_path", "source_document", "university", "degree", "topic", "status"])
        writer.writeheader()
        for path, chunks in sorted(grouped.items()):
            target = OUTPUT / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("\n\n".join(f"Status: {d['status']}\n{d['text']}" for d in chunks), encoding="utf-8")
            writer.writerow({"file_path": path, **{k: chunks[0][k] for k in writer.fieldnames[1:]}})
    for item in items:
        source = source_paths[item["original_path"]]["source_document"]
        replacements = [d for d in records if d["original_path"] is None and d["source_document"] == source]
        item.update(source_document=source, outcome="original_held", replacement_paths=sorted({d["source_path"] for d in replacements}),
                    note="Checked replacement sections are active. This does not mean every passage from this file is reconstructed.",
                    reviewer="Codex; project-owner approved recommendations", review_date="2026-10-27")
        program_pages = {d['page'] for d in replacements if d['topic'] == 'Programs_Majors'}
        if item['review_id'] == 'R003' and {4, 5} <= program_pages:
            item.update(outcome='reconstructed_original_held',
                replacement_paths=sorted({d['source_path'] for d in replacements if d['topic'] == 'Programs_Majors' and d['page'] in (4, 5)}),
                note='Both program-table pages reconstructed: 26 departments on p4 and 22 on p5. Degree-marker totals match the source: 45 masters, 42 doctoral, 36 integrated. Original flattened chunks remain held for traceability.')
        required_pages = {'R004': {4, 10, 11, 17, 20}, 'R005': {16, 19}}
        if item['review_id'] in required_pages:
            pages = required_pages[item['review_id']]
            if pages <= {d['page'] for d in replacements}:
                item.update(outcome='reconstructed_original_held',
                    replacement_paths=sorted({d['source_path'] for d in replacements if d['page'] in pages}),
                    note='Reconstructed against full source sections. Dates, GPA scales and form-specific declarations preserved. Originals remain held; the related fragmented Documents_Verification file is also superseded by pages 7, 9 and 10.')
    (OUTPUT / "REVIEW_LEDGER.json").write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUTPUT / "SOURCE_HASHES.json").write_text(json.dumps(hashes, indent=2, ensure_ascii=False), encoding="utf-8")
    counts = dict(Counter(d["status"] for d in records))
    print(json.dumps({"records": len(records), "status": counts, "review_entries": len(items),
                      "checked_replacement_records": sum(d["original_path"] is None for d in records)}, indent=2))


if __name__ == "__main__":
    build()
