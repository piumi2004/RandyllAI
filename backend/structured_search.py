"""Read-only corpus retrieval and deterministic, scope-aware fee comparisons."""
import os
import re
from collections import defaultdict
from decimal import Decimal

from backend.db import get_connection


def normalize(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def labelled_sources_enabled():
    return os.getenv("STRUCTURED_SOURCE_MODE", "approved").strip().lower() == "labelled"


def resolve_university_names(question):
    text = " " + normalize(question) + " "
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.name, a.alias FROM university.universities u
                LEFT JOIN university.aliases a ON a.university_id=u.id
                WHERE u.active=true
            """)
            names = {r["name"] for r in cur.fetchall()
                     if " " + normalize(r["alias"] or r["name"]) + " " in text}
    return sorted(names)


def question_filters(question):
    q = question.lower()
    degree = None
    for pattern, value in [(r"\b(?:bachelor|bachelors|undergraduate)\b", "Bachelor"),
                           (r"\b(?:master|masters)\b", "Master"),
                           (r"\b(?:ph\.?d|doctoral|doctorate)\b", "Doctoral"),
                           (r"\bassociate\b", "Associate")]:
        if re.search(pattern, q):
            degree = value
            break
    year = re.search(r"\b20\d{2}\b", q)
    period = "year" if re.search(r"annual|per year|yearly|a year", q) else "semester" if "semester" in q else None
    currency = "USD" if re.search(r"\busd\b|dollar|\$", q) else "LKR" if re.search(r"\blkr\b|rupee", q) else "KRW" if re.search(r"\bkrw\b|\bwon\b|₩", q) else None
    budget = re.search(r"(?:under|below|less than|up to|maximum|budget(?: of)?)\s*(?:KRW|USD|LKR|₩|\$)?\s*([\d,]+(?:\.\d+)?)\s*(million|thousand|m\b|k\b)?", q, re.I)
    maximum = None
    if budget:
        multiplier = Decimal(1000000) if budget.group(2) in ("million", "m") else Decimal(1000) if budget.group(2) in ("thousand", "k") else Decimal(1)
        maximum = Decimal(budget.group(1).replace(",", "")) * multiplier
    return {"degree": degree, "year": int(year.group()) if year else None,
            "period": period, "currency": currency, "maximum": maximum,
            "budget_inclusive": bool(budget and re.match(r"up to|maximum|budget", budget.group(), re.I)),
            "language": "English" if "english" in q else "Korean" if "korean taught" in q else None,
            "comparison": bool(re.search(r"compar|cheapest|cheaper|lowest|afford|less expensive|under|below|budget", q))}


def fee_groups(rows):
    """Only exact amounts with matching known units/year/degree may be ranked."""
    groups = defaultdict(list)
    incomplete = []
    for row in rows:
        if (row["billing_period"] == "unknown" or row["effective_year"] is None
                or row.get("is_estimate") or row.get("degree_level") in (None, "Mixed", "Unknown", "Graduate")
                or row.get("amount_max") is not None):
            incomplete.append(row)
            continue
        key = (row["currency"], row["billing_period"], row["effective_year"], row["degree_level"])
        groups[key].append(row)
    output = []
    for key, values in sorted(groups.items()):
        ordered = sorted(values, key=lambda r: (Decimal(r["amount"]), r["university"], r["field_of_study"]))
        amounts = sorted({Decimal(v["amount"]) for v in ordered})
        output.append({"currency": key[0], "billing_period": key[1], "effective_year": key[2],
                       "degree_level": key[3], "scope": "Listed programmes/fields only; not an overall university price",
                       "rows": [{**r, "amount_rank_within_scope": amounts.index(Decimal(r["amount"])) + 1} for r in ordered]})
    return output, incomplete


def summarize_fee_scopes(rows):
    """Retain every institution's range instead of truncating to the first one."""
    buckets = defaultdict(list)
    for row in rows:
        key = (row["university"], row["currency"], row["billing_period"], row["effective_year"], row["degree_level"])
        buckets[key].append(row)
    summaries, representatives = [], []
    for key, values in sorted(buckets.items(), key=lambda item: tuple(str(x) for x in item[0])):
        ordered = sorted(values, key=lambda r: (Decimal(r["amount"]), r["field_of_study"]))
        summaries.append({"university": key[0], "currency": key[1], "billing_period": key[2],
                          "effective_year": key[3], "degree_level": key[4],
                          "minimum_listed": ordered[0]["amount"], "maximum_listed": ordered[-1]["amount"],
                          "listed_records": len(values), "review_statuses": sorted({r["review_status"] for r in values}),
                          "scope": "Range of listed fields only, not all programmes or a guaranteed payable fee"})
        representatives.append(ordered[0])
        if len(ordered) > 1 and ordered[-1] != ordered[0]:
            representatives.append(ordered[-1])
    return summaries, representatives


def get_fee_evidence(question, names):
    filters = question_filters(question)
    conditions = ["t.extraction_status='structured'", "u.active=true"]
    params = []
    if labelled_sources_enabled():
        conditions.append("t.review_status IN ('approved','pending')")
    else:
        conditions.append("t.review_status='approved'")
    for value, expression in [(names, "u.name=ANY(%s)"),
                              (filters["degree"], "t.degree_level=%s"),
                              (filters["year"], "t.effective_year=%s"),
                              (filters["period"], "t.billing_period=%s"),
                              (filters["currency"], "t.currency=%s"),
                              (filters["language"], "p.language_track ILIKE %s")]:
        if value:
            conditions.append(expression)
            params.append("%" + value + "%" if expression.startswith("p.language") else value)
    if filters["maximum"] is not None:
        # A budget needs explicit units; otherwise no meaningful comparison exists.
        if not filters["currency"] or not filters["period"]:
            return {"groups": [], "unranked": [], "notice": "Specify the budget currency and billing period (semester or year) before applying a budget filter.", "filters": filters}
        conditions.append("t.amount <= %s" if filters["budget_inclusive"] else "t.amount < %s")
        params.append(filters["maximum"])
    fields = field_terms(question)
    if fields:
        conditions.append("(" + " OR ".join("t.field_of_study ILIKE %s" for _ in fields) + ")")
        params.extend("%" + word + "%" for word in fields)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.name AS university,t.field_of_study,t.degree_level,t.amount,t.amount_max,
                       t.currency,t.billing_period,t.effective_year,t.is_estimate,t.review_status,
                       t.notes,t.source_page,t.source_locator,s.document_name AS source_document,
                       s.source_type,p.language_track
                FROM financial.tuition_rates t
                JOIN university.universities u ON u.id=t.university_id
                JOIN knowledge.sources s ON s.id=t.source_id
                LEFT JOIN university.academic_programs p ON p.id=t.program_id
                WHERE """ + " AND ".join(conditions) + " ORDER BY u.name,t.degree_level,t.amount,t.field_of_study", params)
            rows = cur.fetchall()
    groups, incomplete = fee_groups(rows)
    summary, _ = summarize_fee_scopes(rows)
    original_count = len(rows)
    if len(rows) > 100:
        _, incomplete = summarize_fee_scopes(incomplete)
        for group in groups:
            group["listed_scope_ranges"], group["rows"] = summarize_fee_scopes(group["rows"])
            group["rows_are_representative_minimum_and_maximum"] = True
    notice = "Only rank within matching currency, billing period, fee year and degree. No exchange conversion or semester-to-year multiplication is assumed."
    if incomplete:
        notice += " Unranked figures lack scope/year/period or are estimates: list them only with those limitations, never call them cheapest."
    if not rows:
        notice += " No eligible structured fees match these filters. Pending/ambiguous extractions may still require review; this is not evidence that no such programme exists."
    return {"groups": groups, "unranked": incomplete, "notice": notice, "filters": filters,
            "listed_scope_ranges": summary, "matching_records": original_count,
            "details_condensed": original_count > 100}


def get_program_evidence(question, names):
    filters = question_filters(question)
    conditions = ["p.active=true", "p.extraction_status='structured'",
                  "p.review_status IN ('approved','pending')" if labelled_sources_enabled() else "p.review_status='approved'"]
    params = []
    for value, expression in [(names, "u.name=ANY(%s)"), (filters["degree"], "p.degree_level=%s"),
                              (filters["language"], "p.language_track ILIKE %s")]:
        if value:
            conditions.append(expression)
            params.append("%" + value + "%" if "ILIKE" in expression else value)
    if filters["year"]:
        conditions.append("p.academic_year=%s")
        params.append(filters["year"])
    fields = field_terms(question)
    if fields:
        conditions.append("(" + " OR ".join("p.program_name ILIKE %s" for _ in fields) + ")")
        params.extend("%" + word + "%" for word in fields)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.name AS university,p.program_name,p.degree_level,p.language_track,
                       p.academic_year,p.review_status,p.source_page,p.source_locator,
                       s.document_name AS source_document
                FROM university.academic_programs p
                JOIN university.universities u ON u.id=p.university_id
                JOIN knowledge.sources s ON s.id=p.source_id
                WHERE """ + " AND ".join(conditions) + " ORDER BY u.name,p.program_name LIMIT 60", params)
            return cur.fetchall()


def field_terms(question):
    return [word for word in ("computer science", "engineering", "business", "medicine", "nursing", "psychology", "music", "art")
            if re.search(r"\b" + re.escape(word) + r"\b", question, re.I)]


def get_cost_evidence(question, names):
    q = question.lower()
    kind = "dormitory" if re.search(r"dorm|housing|accommodation", q) else "admission_fee"
    conditions = ["c.cost_type=%s", "c.review_status IN ('approved','pending')" if labelled_sources_enabled() else "c.review_status='approved'"]
    params = [kind]
    if names:
        conditions.append("u.name=ANY(%s)")
        params.append(names)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT ON (u.name,c.cost_type,c.amount,c.currency,c.billing_period,c.effective_year)
                       u.name AS university,c.cost_type,c.amount,c.currency,c.billing_period,c.effective_year,
                       c.is_estimate,c.review_status,c.source_page,c.source_locator,
                       s.document_name AS source_document
                FROM financial.cost_items c
                JOIN university.universities u ON u.id=c.university_id
                JOIN knowledge.sources s ON s.id=c.source_id
                WHERE """ + " AND ".join(conditions) + " ORDER BY u.name,c.cost_type,c.amount,c.currency,c.billing_period,c.effective_year,c.id LIMIT 80", params)
            return cur.fetchall()


def search_passages(question, names, limit=5):
    # Remove conversational filler while retaining factual terms and proper nouns.
    stop = {"give", "tell", "show", "me", "please", "details", "about", "what", "which", "are", "the", "of", "and", "can", "you", "i", "want", "compare", "university", "universities"}
    terms = [word for word in normalize(question).split() if len(word) > 2 and word not in stop]
    for name in names:
        name_terms = set(normalize(name).split())
        terms = [t for t in terms if t not in name_terms]
    synonyms = {"fees": "tuition OR fee", "tuition": "tuition OR fee", "intakes": "intake OR admission", "intake": "intake OR admission", "scholarships": "scholarship"}
    query = " ".join(synonyms.get(t, t) for t in terms[:10])
    if not query:
        query = "admission"
    status = "p.review_status IN ('approved','pending')" if labelled_sources_enabled() else "p.review_status='approved'"
    params = [query]
    where = [status, "p.extraction_method NOT IN ('needs_ocr_or_visual_review','xlsx_xml','legacy_topic_text')", "length(p.content)>80", "p.search_vector @@ q.query"]
    if names:
        where.append("u.name=ANY(%s)")
        params.append(names)
    params.append(limit)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                WITH q AS (SELECT websearch_to_tsquery('english', %s) AS query)
                SELECT s.document_name AS source_document,p.source_page,p.locator AS source_locator,
                       u.name AS university,p.degree_scope,p.review_status,p.extraction_method,p.quality_notes,
                       ts_headline('english',p.content,q.query,
                           'StartSel=,StopSel=,MaxWords=180,MinWords=80,MaxFragments=2') AS excerpt
                FROM knowledge.source_passages p
                JOIN knowledge.sources s ON s.id=p.source_id
                LEFT JOIN university.universities u ON u.id=p.university_id
                CROSS JOIN q WHERE """ + " AND ".join(where) + " ORDER BY ts_rank_cd(p.search_vector,q.query) DESC,p.id LIMIT %s", params)
            return cur.fetchall()


def retrieve_corpus_evidence(question, names):
    from backend.structured_retrieval import format_database_records
    parts, records = [], []
    numeric = bool(re.search(r"tuition|fee|cost|cheapest|budget", question, re.I))
    other_cost = bool(re.search(r"dorm|housing|accommodation|admission fee", question, re.I))
    if other_cost:
        costs = get_cost_evidence(question, names)
        if costs:
            parts.append("Other source-listed costs: room type, meals, payment duration and applicability require verification. Unknown periods/years and approximate costs must not be ranked as comparable:\n" + format_database_records(costs))
            records.extend(costs)
    if numeric and (not other_cost or "tuition" in question.lower()):
        fees = get_fee_evidence(question, names)
        parts.append("Structured fee comparison (calculated from SQL numeric columns):\n" + format_database_records(fees))
        records.extend(fees["unranked"])
        for group in fees["groups"]:
            records.extend(group["rows"])
    if re.search(r"program|course|degree|major", question, re.I):
        programs = get_program_evidence(question, names)
        if programs:
            parts.append("Structured programme listings (limited to 60; not a complete catalogue):\n" + format_database_records(programs))
            records.extend(programs)
    passages = search_passages(question, names)
    if passages:
        parts.append("PostgreSQL document excerpts (preserve review status and source limitations):\n" + format_database_records(passages))
        records.extend(passages)
    sources = {}
    for row in records:
        locator = row.get("source_locator") or f"physical PDF page {row['source_page']}"
        key = (row["source_document"], locator)
        sources[key] = {"filename": row["source_document"], "page": row.get("source_page") or locator,
                        "source_reference": row["source_document"] + ", " + locator,
                        "source_type": "postgresql", "review_status": row["review_status"]}
    if parts:
        parts.insert(0, "New extractions marked pending are document-sourced, not human-reviewed or certified current. Held records are excluded. Never infer exact dates, missing fee periods, or exchange rates. Compare fees only using the structured comparison groups; do not rank amounts from unrelated prose or unranked rows.")
    return {"context": "\n\n".join(parts), "sources": list(sources.values())}
