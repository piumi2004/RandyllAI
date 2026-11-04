"""Extract the supplied data folder without publishing facts as human-approved.

Run extraction first, then --apply. Original PDFs/XLSX files are never edited.
Qdrant is never written by this importer. Source versions are pinned by SHA-256.
"""
import argparse
import hashlib
import json
import posixpath
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zipfile import ZipFile

import pymupdf
from psycopg.types.json import Jsonb

from backend.db import get_connection

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/ingestion_staging/corpus"
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PDF_IDENTITIES = {
    "Graduate.pdf": ("Kongju National University", "Graduate"),
    "Undergraduate.pdf": ("Kongju National University", "Bachelor"),
    "2.ENG2027-SpringSemesterFreshmanTransferAdmissionGuideline.pdf": ("Gachon University", "Bachelor"),
    "2027-Spring-Semester-Graduate-School-Admissions-Guide-HNU.pdf": ("Hannam University", "Graduate"),
    "Hannam University Bachelor_s.pdf": ("Hannam University", "Bachelor"),
    "Dongseo University.pdf": ("Dongseo University", "Mixed"),
    "Jeonbuk National Bachelor_s.pdf": ("Jeonbuk National University", "Bachelor"),
    "Jeonbuk National Master_s.pdf": ("Jeonbuk National University", "Graduate"),
    "Kyungpook National University Undergraduate.pdf": ("Kyungpook National University", "Bachelor"),
    "HUFS_2027_Spring_Undergraduate_Admission_guide(ENG).pdf": ("Hankuk University of Foreign Studies", "Bachelor"),
    "Tongmyong Bachelor_s.pdf": ("Tongmyong University", "Bachelor"),
    "Tongmyong Master_s.pdf": ("Tongmyong University", "Graduate"),
    "Korean Language Program.pdf": ("Ajou University", "Korean language"),
    "KIT English Recruitment Guideline (1).pdf": ("Kyungnam College of Information and Technology", "Associate"),
    "Kunjang University College.pdf": ("Kunjang University College", "Associate"),
    "Kyungbuk College Timeline and Quota.pdf": ("Kyungbuk College", "Associate"),
    "Woosuk Bachelor_s.pdf": ("Woosuk University", "Bachelor"),
    "Woosong Brochure.pdf": ("Woosong University", "Mixed"),
    "Fall 2026 Jeonju University Graduate School Admissions Guide_For English Track applicants(International students) (1).pdf": ("Jeonju University", "Graduate"),
}
ALIASES = {
    "jeonbuk national university jbnu": "Jeonbuk National University",
    "woosong university wsu south korea": "Woosong University",
    "konju university": "Kongju National University",
    "woosuk university": "Woosuk University",
    "gachon": "Gachon University", "kongju": "Kongju National University",
    "jeonbuk": "Jeonbuk National University", "jbnu": "Jeonbuk National University",
    "kyungpook": "Kyungpook National University", "hufs": "Hankuk University of Foreign Studies",
    "hannam": "Hannam University", "dongseo": "Dongseo University",
    "woosong": "Woosong University", "woosuk": "Woosuk University",
    "jeonju": "Jeonju University", "tongmyong": "Tongmyong University",
    "ajou": "Ajou University", "kit": "Kyungnam College of Information and Technology",
    "kunjang": "Kunjang University College", "kyungbuk": "Kyungbuk College",
    "yeungnam": "Yeungnam University College", "ync": "Yeungnam University College",
    "chungwoon": "Chungwoon University", "konkuk": "Konkuk University", "hanil": "Hanil University",
}


def normalized(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def canonical(name):
    return ALIASES.get(normalized(name), re.sub(r"\s+", " ", name).strip())


def identity(filename):
    if filename in PDF_IDENTITIES:
        return PDF_IDENTITIES[filename]
    if filename.startswith("2027_1"):
        return "Yeungnam University College", "Associate"
    if filename.startswith("Why WSU"):
        degree = "Graduate" if "Graduate" in filename else "Bachelor" if "undergradaute" in filename else "Mixed"
        return "Woosong University", degree
    return None, "General guidance"


def source_record(path, kind, university=None, degree=None):
    return {"name": path.name, "path": path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "kind": kind,
            "university": university, "degree": degree}


def parse_amount(value):
    """Accept one exact decimal only; ranges/formula text are not scalar fees."""
    text = str(value or "").strip()
    if not re.fullmatch(r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?", text):
        return None
    try:
        result = Decimal(text.replace(",", ""))
        return str(result) if 0 <= result < Decimal("100000000000000") else None
    except InvalidOperation:
        return None


def xlsx_sheets(path):
    """Read literal values and preserve formulas; follow workbook relationships."""
    with ZipFile(path) as archive:
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            strings = ["".join(n.itertext()) for n in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall("s:si", NS)]
        relations = {r.attrib["Id"]: r.attrib["Target"] for r in ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))}
        for sheet in ET.fromstring(archive.read("xl/workbook.xml")).find("s:sheets", NS):
            target = relations[sheet.attrib[f"{{{REL}}}id"]]
            member = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
            rows = []
            for row in ET.fromstring(archive.read(member)).findall("s:sheetData/s:row", NS):
                values, formulas = {}, {}
                for cell in row.findall("s:c", NS):
                    address = cell.attrib["r"]
                    column = re.sub(r"\d", "", address)
                    value = cell.find("s:v", NS)
                    text = value.text if value is not None and value.text is not None else ""
                    if cell.attrib.get("t") == "s" and text:
                        text = strings[int(text)]
                    elif cell.attrib.get("t") == "inlineStr":
                        inline = cell.find("s:is", NS)
                        text = "".join(inline.itertext()) if inline is not None else ""
                    values[column] = text
                    formula = cell.find("s:f", NS)
                    if formula is not None:
                        formulas[column] = formula.text or ""
                rows.append({"row": int(row.attrib["r"]), "values": values, "formulas": formulas})
            yield sheet.attrib["name"], rows


def money_observations(text):
    pattern = r"(?:KRW|USD|LKR|₩|\$)\s*[\d,]+(?:\.\d+)?|\d[\d,]*(?:\.\d+)?\s*(?:KRW|USD|LKR|won|%)"
    for i, match in enumerate(re.finditer(pattern, text, re.I)):
        yield {"offset": match.start(), "raw": match.group(),
               "kind": "percentage" if "%" in match.group() else "currency_amount",
               "context": text[max(0, match.start() - 200):match.end() + 280]}


def pdf_tuition_rows(cells, context):
    """Conservative candidates from explicitly labelled tuition rows/columns.

    They remain pending; raw geometry, headers and the full page are retained.
    Never infer a fee's year or period from the admission guide's title.
    """
    if not cells:
        return []
    result = []

    def amount(cell):
        text = str(cell or "")
        if not re.fullmatch(r"[\d,\s]+", text):
            return None
        return parse_amount(re.sub(r"[,\s]", "", text))

    currencies = set(re.findall(r"\b(KRW|USD)\b", context, re.I))
    currency = next(iter(currencies)).upper() if len(currencies) == 1 else None
    if currency is None and re.search(r"\bwon\b|₩", context, re.I) and not re.search(r"\bUSD\b|\$", context):
        currency = "KRW"
    for header_row, row in enumerate(cells[:3]):
        for col, label in enumerate(row):
            if not re.search(r"tuition", str(label or ""), re.I):
                continue
            column_currency = re.search(r"\b(KRW|USD)\b", str(label), re.I)
            unit = column_currency.group(1).upper() if column_currency else currency
            if not unit:
                continue
            for number, body in enumerate(cells[header_row + 1:], header_row + 1):
                if col >= len(body):
                    continue
                value = amount(body[col])
                field = " / ".join(str(c).strip() for c in body[:col] if c)
                if value is not None and Decimal(value) >= 100 and field:
                    result.append({"row": number, "column": col, "field": field,
                                   "amount": value, "currency": unit})
    # Horizontal tables explicitly mark the fee row; column headings carry scope.
    for number, row in enumerate(cells):
        if not row or not re.search(r"tuition", str(row[0] or ""), re.I) or not currency:
            continue
        for col, cell in enumerate(row[1:], 1):
            value = amount(cell)
            label = str(cells[0][col] or "") if col < len(cells[0]) else ""
            if value is not None and Decimal(value) >= 100 and label:
                result.append({"row": number, "column": col, "field": label,
                               "amount": value, "currency": currency})
    # Unit multipliers must be explicit. An unknown/complex multiplier stays raw.
    multiplier = Decimal(1000) if re.search(r"unit\s*:?\s*1[,.]?000\s*(?:KRW|won)|(?:KRW|won)\s*1,000", context, re.I) else Decimal(1)
    unique = {}
    for row in result:
        row["amount"] = str(Decimal(row["amount"]) * multiplier)
        unique[(row["row"], row["column"])] = row
    return list(unique.values())


def extract_pdf(path, emit, problems):
    university, degree = identity(path.name)
    source = source_record(path, "pdf_native", university, degree)
    emit("sources", source)
    with pymupdf.open(path) as pdf:
        for number, page in enumerate(pdf, 1):
            text = page.get_text("text", sort=True)
            quality = "native_text; extraction not human-reviewed"
            method = "pymupdf_native"
            if len(text.strip()) < 80:
                method = "needs_ocr_or_visual_review"
                quality = "Sparse text: scanned content, a cover, or a blank page; not silently skipped"
                problems.append({"source": path.name, "page": number, "reason": quality})
            emit("passages", {"source": source["sha256"], "locator": f"physical PDF page {number}",
                               "page": number, "university": university, "degree": degree,
                               "content": text, "method": method, "quality": quality})
            for obs in money_observations(text):
                emit("observations", {"source": source["sha256"], "page": number,
                                      "locator": f"page {number}, character {obs['offset']}", **obs})
            if method == "needs_ocr_or_visual_review":
                continue
            try:
                finder = page.find_tables()
                for index, table in enumerate(finder.tables):
                    cells = table.extract()
                    emit("tables", {"source": source["sha256"], "page": number,
                                    "locator": f"physical PDF page {number}, detected table {index}",
                                    "university": university, "cells": cells,
                                    "geometry": {"bbox": list(table.bbox), "cells": table.cells},
                                    "context": text, "method": "pymupdf_table; unreviewed_geometry"})
                    if university:
                        for candidate in pdf_tuition_rows(cells, text):
                            emit("costs", {"source": source["sha256"], "university": university,
                                           "program_key": None,
                                           "key": f"pdf/{number}/table/{index}/row/{candidate['row']}/col/{candidate['column']}",
                                           "field": candidate["field"], "degree": degree,
                                           "amount": candidate["amount"], "currency": candidate["currency"],
                                           "kind": "tuition", "period": "unknown", "year": None,
                                           "page": number,
                                           "locator": f"physical PDF page {number}, table {index}, row {candidate['row']}, column {candidate['column']}",
                                           "excerpt": json.dumps({"table": cells, "page_text": text}, ensure_ascii=False),
                                           "estimate": bool(re.search(r"estimate|approx", text, re.I)),
                                           "pdf_candidate": True})
            except Exception as error:
                problems.append({"source": path.name, "page": number, "reason": f"table extraction failed: {error}"})
    if hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
        raise ValueError(f"Source changed during extraction: {path.name}")


def extract_workbook(path, emit, problems):
    source = source_record(path, "spreadsheet")
    emit("sources", source)
    for sheet, rows in xlsx_sheets(path):
        if not rows:
            continue
        headers = rows[0]["values"]
        for row in rows[1:]:
            values, formulas = row["values"], row["formulas"]
            locator = f"worksheet {sheet}, row {row['row']}"
            raw = {"sheet": sheet, "row": row["row"], "cells": values,
                   "headers": headers, "formulas": formulas}
            excerpt = json.dumps(raw, ensure_ascii=False)
            university_name = values.get("A", "").strip()
            major = values.get("B", "").strip()
            university = canonical(university_name) if sheet != "Parameters" and university_name and major else None
            emit("passages", {"source": source["sha256"], "locator": locator, "page": None,
                               "university": university, "degree": values.get("E"), "content": excerpt,
                               "method": "xlsx_xml", "quality": "No source PDF page, applicable year or tuition billing period supplied; formulas are not source facts"})
            emit("tables", {"source": source["sha256"], "locator": locator, "page": None,
                            "university": university, "cells": raw, "geometry": None,
                            "context": excerpt, "method": "xlsx_xml"})
            if not university:
                continue
            flags = [lang for col, lang in (("C", "English"), ("D", "Korean")) if values.get(col, "").lower() == "yes"]
            language = ", ".join(flags) or None
            degree = values.get("E", "").strip() or "Unknown"
            for needle, label in (("bachelor", "Bachelor"), ("master", "Master"), ("phd", "Doctoral"), ("associate", "Associate")):
                if needle in degree.lower():
                    degree = label
                    break
            key = f"{sheet}/row/{row['row']}"
            emit("programs", {"source": source["sha256"], "university": university,
                              "alias": university_name, "key": key, "name": major,
                              "degree": degree, "language": language, "locator": locator, "excerpt": excerpt})
            for col, header in headers.items():
                currency_match = re.search(r"\b(KRW|USD)\b", header)
                if not currency_match or col in formulas:
                    continue
                amount = parse_amount(values.get(col))
                if amount is None:
                    if values.get(col):
                        problems.append({"source": path.name, "locator": locator + ", column " + col,
                                         "reason": "Non-scalar money value preserved in raw row; not treated as an exact fee"})
                    continue
                kind = "tuition" if "tuition fee" in header.lower() else "dormitory" if "dorm" in header.lower() else "admission_fee" if "admission" in header.lower() else None
                if not kind:
                    continue
                emit("costs", {"source": source["sha256"], "university": university,
                               "program_key": key, "key": key + "/" + col,
                               "field": major, "degree": degree, "amount": amount,
                               "currency": currency_match.group(1), "kind": kind,
                               "period": "unknown", "year": None, "locator": locator + ", cell " + col + str(row["row"]),
                               "excerpt": excerpt, "estimate": "approx" in header.lower()})
    if hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
        raise ValueError("Spreadsheet changed during extraction")


def extract_corpus():
    OUT.mkdir(parents=True, exist_ok=True)
    names = ("sources", "passages", "tables", "observations", "programs", "costs")
    handles = {name: (OUT / f"{name}.jsonl").open("w", encoding="utf-8") for name in names}
    counts, problems = Counter(), []

    def emit(name, record):
        handles[name].write(json.dumps(record, ensure_ascii=False) + "\n")
        counts[name] += 1

    try:
        for path in sorted((ROOT / "data/pdfs").glob("*.pdf")):
            print("Extracting", ascii(path.name), flush=True)
            extract_pdf(path, emit, problems)
        for path in sorted((ROOT / "data/structured").glob("*.xlsx")):
            extract_workbook(path, emit, problems)
        # Existing OCR artifacts have no reliable physical-page map. Preserve
        # Markdown locations instead of inventing PDF page citations.
        for path in sorted((ROOT / "data/ocr_output").glob("*.md")):
            university, degree = identity(path.with_suffix(".pdf").name)
            source = source_record(path, "ocr_markdown", university, degree)
            emit("sources", source)
            text = path.read_text(encoding="utf-8")
            lines = text.splitlines(keepends=True)
            for start in range(0, len(lines), 35):
                emit("passages", {"source": source["sha256"], "locator": f"OCR Markdown lines {start+1}–{min(start+35,len(lines))}",
                                   "page": None, "university": university, "degree": degree,
                                   "content": "".join(lines[start:start+35]), "method": "existing_ocr_markdown",
                                   "quality": "OCR may contain recognition errors; physical PDF page mapping unavailable"})
        # Retain topic extractions too, including curated source notes. These
        # are never silently promoted to independent source documents.
        base = ROOT / "data/Randyll_Semantic_Knowledge"
        for path in sorted(base.rglob("*.txt")):
            text = path.read_text(encoding="utf-8-sig")
            source = source_record(path, "legacy_topic_text")
            emit("sources", source)
            for index, start in enumerate(range(0, len(text), 5000), 1):
                emit("passages", {"source": source["sha256"], "locator": f"topic extraction characters {start}–{min(start+5000,len(text))}",
                                   "page": None, "university": None, "degree": None,
                                   "content": text[start:start+5000], "method": "legacy_topic_text",
                                   "quality": "Derived legacy extraction; original PDF identity/page must be checked"})
    finally:
        for handle in handles.values():
            handle.close()
    report = {"counts": dict(counts), "issues": problems, "qdrant_writes": 0,
              "new_record_review_status": "pending", "original_files_modified": False}
    (OUT / "EXTRACTION_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"counts": dict(counts), "issues": len(problems)}, indent=2), flush=True)
    return report


def read_records(name):
    with (OUT / f"{name}.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            yield json.loads(line)


def postgres_safe(value):
    """Represent NUL visibly: PostgreSQL cannot store it in text or JSONB.

    The unmodified PDF and raw extraction JSONL remain the primary artifacts.
    """
    if isinstance(value, str):
        return value.replace("\x00", "\\u0000")
    if isinstance(value, list):
        return [postgres_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: postgres_safe(item) for key, item in value.items()}
    return value


def database_records(name):
    for record in read_records(name):
        if name == "passages" and "\x00" in record["content"]:
            record["quality"] += "; embedded NUL represented visibly as literal \\u0000 in PostgreSQL; raw artifact unchanged"
        yield postgres_safe(record)


def refresh_pdf_fees():
    """Reparse staged tables without rerunning PDF geometry detection."""
    sources = {s["sha256"]: s for s in read_records("sources")}
    plans = json.loads((ROOT / "backend/knowledge_review_sections.json").read_text(encoding="utf-8"))
    scope_by_page = {(p["source"], p["page"]): p["scope"] for p in plans if p["topic"] == "Tuition_Fees"}
    costs = [row for row in read_records("costs") if not row.get("pdf_candidate")]
    for table in read_records("tables"):
        source = sources[table["source"]]
        if source["kind"] != "pdf_native" or not table["university"]:
            continue
        name = "YEUNGNAM" if source["name"].startswith("2027_1") else source["name"]
        scope = scope_by_page.get((name, table["page"]), "")
        year = re.search(r"\b(20\d{2})\b", scope)
        for candidate in pdf_tuition_rows(table["cells"], table["context"]):
            key = f"{table['locator']}/row/{candidate['row']}/col/{candidate['column']}"
            costs.append({"source": table["source"], "university": table["university"],
                          "program_key": None, "key": key, "field": candidate["field"],
                          "degree": source["degree"], "amount": candidate["amount"],
                          "currency": candidate["currency"], "kind": "tuition",
                          "period": "semester" if re.search(r"per semester", scope, re.I) else "unknown",
                          "year": int(year.group(1)) if year else None, "page": table["page"],
                          "locator": key, "excerpt": json.dumps({"table": table["cells"], "page_text": table["context"], "historical_scope": scope}, ensure_ascii=False),
                          "estimate": bool(re.search(r"estimate|approx", table["context"], re.I)),
                          "pdf_candidate": True})
    (OUT / "costs.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in costs), encoding="utf-8")
    report = json.loads((OUT / "EXTRACTION_REPORT.json").read_text(encoding="utf-8"))
    report["counts"]["costs"] = len(costs)
    report["pdf_tuition_candidates"] = sum(bool(r.get("pdf_candidate")) for r in costs)
    (OUT / "EXTRACTION_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def apply_corpus():
    # A single transaction prevents a half-imported dataset from becoming visible.
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute((ROOT / "db/schema.sql").read_text(encoding="utf-8"))
            cur.execute((ROOT / "db/002_corpus.sql").read_text(encoding="utf-8"))
            universities, sources, programs = {}, {}, {}

            def university_id(name):
                if not name:
                    return None
                if name not in universities:
                    cur.execute("INSERT INTO university.universities(name) VALUES (%s) ON CONFLICT(name) DO NOTHING", (name,))
                    cur.execute("SELECT id FROM university.universities WHERE name=%s", (name,))
                    universities[name] = cur.fetchone()["id"]
                    cur.execute("INSERT INTO university.aliases(alias,university_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (normalized(name), universities[name]))
                return universities[name]

            for row in database_records("sources"):
                path = ROOT / row["path"]
                if hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
                    raise ValueError("Source changed after extraction: " + row["name"])
                cur.execute("""INSERT INTO knowledge.sources(document_name,file_path,sha256,source_type)
                               VALUES (%s,%s,%s,%s) ON CONFLICT(sha256) DO NOTHING""",
                            (row["name"], row["path"], row["sha256"], row["kind"]))
                cur.execute("SELECT id FROM knowledge.sources WHERE sha256=%s", (row["sha256"],))
                sources[row["sha256"]] = cur.fetchone()["id"]
                university_id(row.get("university"))
            for row in database_records("passages"):
                cur.execute("""INSERT INTO knowledge.source_passages
                               (source_id,locator,source_page,university_id,degree_scope,content,extraction_method,quality_notes)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(source_id,locator) DO NOTHING""",
                            (sources[row["source"]], row["locator"], row["page"], university_id(row["university"]),
                             row["degree"], row["content"], row["method"], row["quality"]))
            for row in database_records("tables"):
                cur.execute("""INSERT INTO knowledge.source_tables
                               (source_id,source_page,locator,university_id,cells,geometry,context,extraction_method)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(source_id,locator) DO NOTHING""",
                            (sources[row["source"]], row["page"], row["locator"], university_id(row["university"]),
                             Jsonb(row["cells"]), Jsonb(row["geometry"]), row["context"], row["method"]))
            for row in database_records("observations"):
                cur.execute("""INSERT INTO knowledge.numeric_observations
                               (source_id,locator,source_page,raw_value,context,kind)
                               VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT(source_id,locator) DO NOTHING""",
                            (sources[row["source"]], row["locator"], row["page"], row["raw"], row["context"], row["kind"]))
            for row in database_records("programs"):
                uid, sid = university_id(row["university"]), sources[row["source"]]
                cur.execute("INSERT INTO university.aliases(alias,university_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (normalized(row["alias"]), uid))
                cur.execute("""INSERT INTO university.academic_programs
                               (university_id,program_name,degree_level,language_track,source_id,
                                source_locator,source_excerpt,record_key,review_notes)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(source_id,record_key) DO NOTHING""",
                            (uid, row["name"], row["degree"], row["language"], sid, row["locator"], row["excerpt"], row["key"],
                             "Spreadsheet source; programme offering, applicable year, language and PDF provenance require review."))
                cur.execute("SELECT id FROM university.academic_programs WHERE source_id=%s AND record_key=%s", (sid, row["key"]))
                programs[(row["source"], row["key"])] = cur.fetchone()["id"]
            for row in database_records("costs"):
                sid, uid = sources[row["source"]], university_id(row["university"])
                pid = programs.get((row["source"], row["program_key"]))
                if row["kind"] == "tuition":
                    cur.execute("""INSERT INTO financial.tuition_rates
                                   (source_id,university_id,program_id,record_key,field_of_study,degree_level,
                                    amount,currency,billing_period,effective_year,source_locator,source_excerpt,
                                    source_page,extraction_status,
                                    is_estimate,notes,review_notes)
                                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                   ON CONFLICT(source_id,record_key) DO NOTHING""",
                                (sid, uid, pid, row["key"], row["field"], row["degree"], row["amount"], row["currency"],
                                 row["period"], row["year"], row["locator"], row["excerpt"], row.get("page"),
                                 "ambiguous" if row.get("pdf_candidate") else "structured", row["estimate"],
                                 "Year and billing period require verification; do not assume per-semester or annual.",
                                 "Pending source verification. PDF geometry candidates require inspection. Converted LKR values are not original fees."))
                else:
                    cur.execute("""INSERT INTO financial.cost_items
                                   (source_id,university_id,program_id,record_key,cost_type,amount,currency,
                                    source_locator,source_excerpt,is_estimate)
                                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                   ON CONFLICT(source_id,record_key) DO NOTHING""",
                                (sid, uid, pid, row["key"], row["kind"], row["amount"], row["currency"], row["locator"], row["excerpt"], row["estimate"]))
            for alias, name in ALIASES.items():
                if name in universities:
                    cur.execute("INSERT INTO university.aliases(alias,university_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (alias, universities[name]))
            cur.execute((ROOT / "db/003_review_views.sql").read_text(encoding="utf-8"))
    print("Corpus import committed; existing approvals preserved; Qdrant unchanged.", flush=True)


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extract", action="store_true", help="Read originals and write review artifacts")
    parser.add_argument("--apply", action="store_true", help="Import staged artifacts into PostgreSQL")
    args = parser.parse_args()
    if not (args.extract or args.apply):
        parser.error("Choose --extract and/or --apply")
    if args.extract:
        extract_corpus()
    if args.apply:
        refresh_pdf_fees()
        apply_corpus()


if __name__ == "__main__":
    main()
