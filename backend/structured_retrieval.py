
import json
import re
from decimal import Decimal
from datetime import date, datetime

from backend.db import (
    get_programs,
    get_tuition,
    get_intakes,
    get_general_intakes,
    get_agency_services,
    has_pending_agency_services,
)


def format_database_records(records):
    """Convert PostgreSQL records into LLM-readable text."""
    return json.dumps(
        records,
        indent=2,
        default=lambda obj: (
            str(obj)
            if isinstance(obj, Decimal)
            else obj.isoformat()
            if isinstance(obj, (date, datetime))
            else str(obj)
        ),
    )


def retrieve_structured_context(
    question: str,
    university_name: str = None
) -> str:
    return retrieve_structured_evidence(question, university_name)["context"]


def is_agency_service_question(question):
    normalized = re.sub(r"[^a-z0-9]+", " ", question.lower()).strip()
    tokens = normalized.split()
    # Covers "Our servicese" without matching unrelated university subjects.
    if normalized in {"agency details", "agency services", "agency", "services"}:
        return True
    if len(tokens) == 2 and tokens[0] in {"our", "your"} and tokens[1].startswith("service"):
        return True
    return "randyll" in tokens and (
        normalized in {"randyll", "randyll overseas", "randyll oversese"}
        or any(word in tokens for word in ("choose", "agency", "details", "about", "offer", "offers",
                                           "provide", "provides", "support", "sop", "ielts"))
        or any(word.startswith("service") for word in tokens)
    )


def retrieve_structured_evidence(question: str, university_name: str = None, *,
                                 university_names=None, include_corpus=False):
    """Return approved facts with citations; general facts never imply university dates."""
    q = question.lower()
    groups = []
    service_review_pending = False
    names = university_names if university_names is not None else ([university_name] if university_name else [])
    intake_question = any(word in q for word in (
        "deadline", "intake", "application date", "admission period", "addmission period"))
    if names:
        for name in names:
            if not include_corpus and any(word in q for word in ("tuition", "fee", "cost")):
                groups.append((f"tuition for {name}", get_tuition(name)))
            if intake_question:
                rows = get_intakes(name)
                if include_corpus:
                    from backend.structured_search import question_filters
                    filters = question_filters(question)
                    rows = [r for r in rows if (not filters["year"] or r["academic_year"] == filters["year"])
                            and (not filters["degree"] or r["degree_level"] == filters["degree"])]
                groups.append((f"university admissions for {name}", rows))
            if not include_corpus and any(word in q for word in ("program", "course", "degree", "major")):
                groups.append((f"programs for {name}", get_programs(name)))
    else:
        if intake_question:
            groups.append(("general intake guidance; not university-specific deadlines", get_general_intakes()))
        if is_agency_service_question(question):
            services = get_agency_services()
            groups.append(("agency's stated services; not independent outcome claims", services))
            service_review_pending = not services and has_pending_agency_services()
    context = []
    sources = {}
    for category, records in groups:
        if not records:
            continue
        context.append(f"Structured PostgreSQL records ({category}):\n{format_database_records(records)}")
        for row in records:
            pages = row.get("source_pages") or ([row["source_page"]] if row.get("source_page") else [])
            document = row["source_document"]
            locator = row.get("source_locator") or "physical PDF pages " + ", ".join(map(str, pages))
            key = (document, locator)
            sources[key] = {
                "filename": document, "page": ", ".join(map(str, pages)) if pages else locator,
                "source_reference": f"{document}, {locator}",
                "source_type": "postgresql", "category": category,
            }
    evidence = {"context": "\n\n".join(context), "sources": list(sources.values())}
    if not context and service_review_pending:
        evidence["answer"] = (
            "Randyll Overseas service details have been uploaded, but are awaiting "
            "review and approval. They are not available for chatbot answers yet."
        )
    if include_corpus and not is_agency_service_question(question):
        from backend.structured_search import retrieve_corpus_evidence
        corpus = retrieve_corpus_evidence(question, names)
        evidence["context"] = "\n\n".join(part for part in (evidence["context"], corpus["context"]) if part)
        combined = evidence["sources"] + corpus["sources"]
        evidence["sources"] = list({(s["filename"], s["source_reference"]): s for s in combined}.values())
    return evidence
