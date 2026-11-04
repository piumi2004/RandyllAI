"""Detect and replace university guide vectors in Qdrant."""
import hashlib
import os
import re
import uuid
from pathlib import Path
from urllib.parse import urlparse

import pymupdf
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

from backend.knowledge_domains import TAXONOMY, UPLOAD_COLLECTION, classify_topic
from backend.knowledge_loader import split_text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EMBEDDING_MODEL = "BAAI/bge-m3"
MAX_FILE_BYTES = 50 * 1024 * 1024
BATCH_SIZE = 8
DEFAULT_PRIMARY_COLLECTION = "randyll_korea_knowledge_v2"

UNIVERSITIES = {
    "dongseo": "Dongseo University",
    "jeonbuk": "Jeonbuk National University",
    "kyungpook": "Kyungpook National University",
    "kongju": "Kongju National University",
    "gachon": "Gachon University",
    "yeungnam university": "Yeungnam University",
    "yeungnam university college": "Yeungnam University College",
    "ajou": "Ajou University",
    "tongmyong": "Tongmyong University",
    "hannam": "Hannam University",
    "hankuk university of foreign studies": "Hankuk University of Foreign Studies",
    "woosong": "Woosong University",
    "woosuk": "Woosuk University",
    "kunjang": "Kunjang University College",
    "jeonju": "Jeonju University",
    "kyungbuk": "Kyungbuk University",
}

UNIVERSITY_ALIASES = {
    "dongseo": ["dongseo", "dongseo university", "동서대학교"],
    "jeonbuk": [
        "jeonbuk national university", "jeonbuk university", "jeonbuk",
        "chonbuk", "jbnu", "전북대학교",
    ],
    "kyungpook": [
        "kyungpook national university", "kyungpook university",
        "kyungpook", "경북대학교",
    ],
    "kongju": ["kongju national university", "kongju university", "kongju", "공주대학교"],
    "gachon": ["gachon university", "gachon", "가천대학교"],
    "yeungnam university": ["yeungnam university", "yeungnam", "영남대학교"],
    "yeungnam university college": [
        "yeungnam university college", "ync", "영남이공대학교",
    ],
    "ajou": ["ajou university", "ajou", "아주대학교"],
    "tongmyong": ["tongmyong university", "tongmyong", "동명대학교"],
    "hannam": ["hannam university", "hannam", "한남대학교"],
    "hankuk university of foreign studies": [
        "hankuk university of foreign studies", "hufs", "한국외국어대학교",
    ],
    "woosong": ["woosong university", "woosong", "우송대학교"],
    "woosuk": ["woosuk university", "woosuk", "우석대학교"],
    "kunjang": [
        "kunjang university college", "kunjang", "군장대학교",
    ],
    "jeonju": ["jeonju university", "jeonju", "전주대학교"],
    "kyungbuk": ["kyungbuk university", "kyungbuk", "경북전문대학교"],
}

GUIDE_CATEGORIES = {
    "Admission guidelines": {
        "id": "admission_guidelines",
        "topics": [
            "Application_Fee",
            "Documents_Academic",
            "Documents_Identity",
            "Documents_Verification",
            "Documents_Required",
            "Eligibility_Academic",
            "Eligibility_Language",
            "Eligibility_Nationality",
            "Financial_Proof",
            "Interviews_Assessment",
            "Application_Deadlines",
            "Application_Procedure",
            "Admission_Results",
            "Admission_Policies",
            "Application_Forms",
            "Privacy_Consent",
            "Academic_Grading",
        ],
        "keywords": [
            "admission guideline", "admission guide", "admissions",
            "admission", "application guideline", "application procedure",
            "freshman admission", "모집요강", "입학전형", "입학 안내",
            "신입학", "입학",
        ],
    },
    "Tuition and fees": {
        "id": "tuition_and_fees",
        "topics": ["Tuition_Fees"],
        "keywords": [
            "tuition and fees", "tuition fee", "tuition", "fee schedule",
            "tuition fees", "등록금", "수업료",
        ],
    },
    "Scholarships": {
        "id": "scholarships",
        "topics": ["Scholarships_Admission", "Scholarships_Other"],
        "keywords": ["scholarships", "scholarship", "장학금"],
    },
    "Visa and immigration": {
        "id": "visa_and_immigration",
        "topics": ["Visa_Immigration"],
        "keywords": ["immigration", "visa", "비자", "사증"],
    },
    "Housing and dormitories": {
        "id": "housing_and_dormitories",
        "topics": ["Housing_Dormitory"],
        "keywords": [
            "dormitory", "dormitories", "housing", "residence hall",
            "기숙사", "생활관",
        ],
    },
}

DEGREE_KEYWORDS = {
    "Undergraduate": [
        "undergraduate", "bachelor", "freshman", "transfer admission",
        "학부", "학사", "신입학",
    ],
    "Graduate": ["graduate school", "graduate", "master", "대학원", "석사"],
    "Doctoral": ["doctoral", "doctorate", "phd", "ph.d", "박사"],
    "Non-degree": [
        "non-degree", "korean language program", "language program",
        "어학당", "한국어 연수",
    ],
}

INTAKE_KEYWORDS = {
    "Spring": ["spring admission", "spring semester", "spring intake", "봄학기", "전기"],
    "Fall": ["fall admission", "fall semester", "fall intake", "autumn intake", "가을학기", "후기"],
}


def create_qdrant_client():
    load_dotenv(PROJECT_ROOT / ".env", override=True)
    cloud_url = os.getenv("QDRANT_CLOUD_URL", "").strip()
    cloud_key = os.getenv("QDRANT_CLOUD_API_KEY", "").strip()
    url = cloud_url or os.getenv("QDRANT_URL", "").strip() or "http://localhost:6333"
    api_key = cloud_key if cloud_url else os.getenv("QDRANT_API_KEY", "").strip()
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.hostname:
        raise ValueError("Qdrant URL in .env must be a valid HTTP or HTTPS URL.")
    is_local = parsed_url.hostname.lower() in {"localhost", "127.0.0.1", "::1"}
    if not is_local and parsed_url.scheme != "https":
        raise ValueError("Remote Qdrant connections must use HTTPS.")
    if not is_local and not api_key:
        raise ValueError("Qdrant API key is missing from the project .env file.")
    return QdrantClient(url=url, api_key=api_key or None, timeout=120)


def primary_collection_name():
    load_dotenv(PROJECT_ROOT / ".env", override=True)
    return os.getenv("QDRANT_COLLECTION", DEFAULT_PRIMARY_COLLECTION).strip()


def extract_pages(filename, content):
    if Path(filename).suffix.lower() != ".pdf":
        raise ValueError("Upload a PDF guide.")
    if not content:
        raise ValueError("The uploaded PDF is empty.")
    if len(content) > MAX_FILE_BYTES:
        raise ValueError("The PDF exceeds the 50 MB upload limit.")
    try:
        with pymupdf.open(stream=content, filetype="pdf") as document:
            if document.needs_pass:
                raise ValueError("This PDF is password-protected and cannot be indexed.")
            image_only_pages = []
            pages = []
            for page_number, page in enumerate(document, start=1):
                text = page.get_text("text").strip()
                if text:
                    pages.append({"page": page_number, "text": text})
                elif page.get_images():
                    image_only_pages.append(page_number)
    except pymupdf.FileDataError as error:
        raise ValueError("Unable to read this PDF. Check that the file is valid.") from error
    if image_only_pages:
        numbers = ", ".join(str(number) for number in image_only_pages)
        raise ValueError(
            f"PDF page(s) {numbers} contain images without selectable text. "
            "Run OCR on these pages before uploading."
        )
    if not pages:
        raise ValueError("No selectable text was found in the PDF. Run OCR before uploading.")
    return pages


def extract_document_pages(filename, content):
    extension = Path(filename).suffix.lower()
    if extension == ".pdf":
        return extract_pages(filename, content)
    if extension not in {".txt", ".md"}:
        raise ValueError("Upload a PDF, TXT, or Markdown document.")
    if not content:
        raise ValueError("The uploaded document is empty.")
    if len(content) > MAX_FILE_BYTES:
        raise ValueError("The document exceeds the 50 MB upload limit.")
    try:
        text = content.decode("utf-8-sig").strip()
    except UnicodeDecodeError as error:
        raise ValueError("Text and Markdown documents must use UTF-8 encoding.") from error
    if not text:
        raise ValueError("The uploaded document contains no text.")
    return [{"page": 1, "text": text}]


def _normalize(value):
    return re.sub(r"\s+", " ", str(value or "").casefold()).strip()


def _contains_term(text, term):
    escaped = re.escape(term.casefold())
    if term.isascii() and term[:1].isalnum():
        return re.search(r"(?<![a-z0-9])" + escaped + r"(?![a-z0-9])", text) is not None
    return escaped in text


def _university_mentions(text):
    matches = []
    for university_id, aliases in UNIVERSITY_ALIASES.items():
        for alias in aliases:
            normalized_alias = _normalize(alias)
            escaped = re.escape(normalized_alias)
            if alias.isascii() and alias[:1].isalnum():
                pattern = re.compile(r"(?<![a-z0-9])" + escaped + r"(?![a-z0-9])")
            else:
                pattern = re.compile(escaped)
            matches.extend(
                (university_id, match) for match in pattern.finditer(text)
            )

    non_overlapping = []
    for university_id, match in sorted(
        matches,
        key=lambda item: (-(item[1].end() - item[1].start()), item[1].start()),
    ):
        if all(
            match.start() >= existing.end() or match.end() <= existing.start()
            for _, existing in non_overlapping
        ):
            non_overlapping.append((university_id, match))
    counts = {university_id: 0 for university_id in UNIVERSITY_ALIASES}
    for university_id, _ in non_overlapping:
        counts[university_id] += 1
    return counts


def _detect_university(filename, pages):
    scores = {university_id: 0 for university_id in UNIVERSITY_ALIASES}
    normalized_filename = _normalize(Path(filename).stem.replace("_", " "))
    filename_mentions = _university_mentions(normalized_filename)
    for university_id, count in filename_mentions.items():
        scores[university_id] += 10 * count

    for page_number, page in enumerate(pages, start=1):
        weight = 5 if page_number == 1 else 3 if page_number == 2 else 1
        normalized_page = _normalize(page["text"])
        page_mentions = _university_mentions(normalized_page)
        for university_id, count in page_mentions.items():
            scores[university_id] += weight * count

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    if not ranked or ranked[0][1] == 0:
        raise ValueError(
            "Could not identify one supported university from the PDF text. "
            "Include the university name in the filename or ensure it appears "
            "as selectable text somewhere in the document."
        )
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        raise ValueError(
            "The PDF mentions multiple supported universities with similar "
            "evidence, so the replacement target is ambiguous. Upload a guide "
            "for one university at a time."
        )
    return ranked[0][0]


def _detect_year(filename, first_page_text):
    filename_years = sorted(set(re.findall(r"\b20(?:2\d|[3-9]\d)\b", filename)))
    if len(filename_years) > 1:
        raise ValueError("The filename contains multiple academic years; rename it clearly.")

    text = first_page_text[:5000]
    explicit_years = sorted(set(re.findall(
        r"\b(20(?:2\d|[3-9]\d))\s*(?:학년도|academic\s+year)",
        text,
        flags=re.IGNORECASE,
    )))
    if filename_years:
        filename_year = int(filename_years[0])
        if explicit_years and any(int(year) != filename_year for year in explicit_years):
            raise ValueError(
                "The academic year in the filename conflicts with the guide title."
            )
        return filename_year

    page_years = explicit_years or sorted(set(
        re.findall(r"\b20(?:2\d|[3-9]\d)\b", text)
    ))
    if len(page_years) != 1:
        raise ValueError(
            "Could not determine one academic year from the PDF filename and first page. "
            "Include a single year such as 2027 in the filename."
        )
    return int(page_years[0])


def _infer_year_for_incremental_sync(filename, first_page_text):
    filename_years = sorted(set(re.findall(
        r"\b20(?:2\d|[3-9]\d)\b",
        filename,
    )))
    if len(filename_years) > 1:
        return None

    text = first_page_text[:5000]
    explicit_years = sorted(set(re.findall(
        r"\b(20(?:2\d|[3-9]\d))\s*(?:학년도|academic\s+year)",
        text,
        flags=re.IGNORECASE,
    )))
    if len(explicit_years) > 1:
        return None
    if filename_years and explicit_years:
        if filename_years[0] != explicit_years[0]:
            raise ValueError(
                "The academic year in the filename conflicts with the guide title."
            )
        return int(filename_years[0])
    if filename_years:
        return int(filename_years[0])
    if explicit_years:
        return int(explicit_years[0])

    page_years = sorted(set(re.findall(r"\b20(?:2\d|[3-9]\d)\b", text)))
    return int(page_years[0]) if len(page_years) == 1 else None


def _keyword_score(text, filename, terms):
    score = 0
    for term in terms:
        normalized_term = _normalize(term)
        if _contains_term(_normalize(filename), normalized_term):
            score += 5
        if _contains_term(text, normalized_term):
            score += 1
    return score


def _detect_category(filename, first_page_text):
    text = _normalize(first_page_text[:10000])
    scores = {
        label: _keyword_score(text, filename, category["keywords"])
        for label, category in GUIDE_CATEGORIES.items()
    }
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    if not ranked or ranked[0][1] == 0:
        raise ValueError(
            "Could not identify the guide category from the filename and first page."
        )
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        raise ValueError(
            "The PDF category is ambiguous. Use a clearer filename or guide title."
        )
    return ranked[0][0]


def _detect_degree(filename, first_page_text):
    text = _normalize(f"{filename}\n{first_page_text[:5000]}")
    found = [
        degree for degree, terms in DEGREE_KEYWORDS.items()
        if any(_contains_term(text, _normalize(term)) for term in terms)
    ]
    if len(found) > 1:
        raise ValueError(
            "The PDF mentions multiple degree levels, so the replacement scope "
            "is ambiguous. Upload one degree-level guide at a time."
        )
    if found:
        return found[0]
    if any(_contains_term(text, term) for term in (
        "all degree levels", "all programs", "all programmes", "all applicants",
        "전체 학위", "전 과정",
    )):
        return "All degree levels"
    raise ValueError(
        "Could not determine one degree level from the PDF. Include undergraduate, "
        "graduate, doctoral, or non-degree in the title or filename."
    )


def _detect_intake(filename, first_page_text):
    text = _normalize(f"{filename}\n{first_page_text[:5000]}")
    found = [
        intake for intake, terms in INTAKE_KEYWORDS.items()
        if any(_contains_term(text, _normalize(term)) for term in terms)
    ]
    return found[0] if len(found) == 1 else "All intakes"


def analyze_guide(filename, content):
    pages = extract_pages(filename, content)
    first_page = pages[0]["text"]
    university_id = _detect_university(filename, pages)
    return {
        "filename": Path(filename).name,
        "sha256": hashlib.sha256(content).hexdigest(),
        "university_id": university_id,
        "university": UNIVERSITIES[university_id],
        "academic_year": _detect_year(filename, first_page),
        "category_label": _detect_category(filename, first_page),
        "degree_level": _detect_degree(filename, first_page),
        "intake_scope": _detect_intake(filename, first_page),
        "page_count": len(pages),
        "character_count": sum(len(page["text"]) for page in pages),
    }


def _replacement_scope(metadata):
    category = GUIDE_CATEGORIES[metadata["category_label"]]
    return {
        "university_id": metadata["university_id"],
        "category": category["id"],
        "topics": category["topics"],
        "degree_level": metadata["degree_level"],
    }


def _canonical_topic(value):
    topic, _, _ = classify_topic(str(value or "").replace(" ", "_"))
    return topic if topic in TAXONOMY["topics"] else None


def _university_id_from_value(value):
    normalized = _normalize(str(value).replace("_", " "))
    for university_id, display_name in UNIVERSITIES.items():
        aliases = UNIVERSITY_ALIASES[university_id]
        if normalized in {_normalize(university_id), _normalize(display_name)}:
            return university_id
        if normalized in {_normalize(alias) for alias in aliases}:
            return university_id
    return None


def _legacy_university_id(payload):
    explicit = _university_id_from_value(
        payload.get("university_id") or payload.get("university", "")
    )
    if explicit:
        return explicit
    parts = str(payload.get("source_path") or "").replace("\\", "/").split("/")
    if parts and parts[0] == "Randyll_Semantic_Knowledge":
        parts = parts[1:]
    if parts and parts[0] == "CURATED_FACT_SHEETS":
        parts = parts[1:]
    return _university_id_from_value(parts[0]) if parts else None


def _legacy_degree(payload):
    value = str(payload.get("degree_level") or payload.get("degree") or "")
    parts = str(payload.get("source_path") or "").replace("\\", "/").split("/")
    if not value or value == "Example University":
        if parts and parts[0] == "Randyll_Semantic_Knowledge":
            parts = parts[1:]
        if parts and parts[0] == "CURATED_FACT_SHEETS":
            value = " ".join(Path(part).stem.replace("_", " ") for part in parts[1:])
        elif len(parts) > 1:
            value = parts[1]
    normalized = _normalize(value)
    if any(term in normalized for term in ("undergraduate", "bachelor", "under grad")):
        return "Undergraduate"
    if any(term in normalized for term in ("doctoral", "phd", "doctorate")):
        return "Doctoral"
    if any(term in normalized for term in ("graduate", "master")):
        return "Graduate"
    if "non degree" in normalized or "language program" in normalized:
        return "Non-degree"
    return "All degree levels"


def _matches_replacement(payload, scope):
    if payload.get("status", "active") != "active":
        return False
    if _legacy_university_id(payload) != scope["university_id"]:
        return False
    if scope["degree_level"] != "All degree levels":
        if _legacy_degree(payload) != scope["degree_level"]:
            return False
    topics = set(scope["topics"])
    replacement_topics = payload.get("replacement_topics") or []
    if set(replacement_topics) & topics:
        return True
    topic = _canonical_topic(payload.get("topic"))
    if topic in topics:
        return True
    source_path = str(payload.get("source_path") or "").replace("\\", "/")
    if source_path and not payload.get("topic"):
        source_topic = _canonical_topic(Path(source_path).stem)
        return source_topic in topics
    return False


def _scroll_matching_points(client, collection, scope, with_vectors):
    if not client.collection_exists(collection):
        return []
    matching_points = []
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=collection,
            limit=128,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        matching_points.extend(
            point for point in points
            if _matches_replacement(point.payload or {}, scope)
        )
        if offset is None:
            break
    if not with_vectors or not matching_points:
        return matching_points

    snapshots = []
    for start in range(0, len(matching_points), 128):
        snapshots.extend(client.retrieve(
            collection_name=collection,
            ids=[point.id for point in matching_points[start:start + 128]],
            with_payload=True,
            with_vectors=True,
        ))
    if {str(point.id) for point in snapshots} != {
        str(point.id) for point in matching_points
    }:
        raise RuntimeError(
            f"Could not back up every matching vector from {collection}."
        )
    return snapshots


def inspect_replacement_targets(client, metadata, primary_collection):
    if not client.collection_exists(primary_collection):
        raise ValueError(
            f"The configured knowledge collection '{primary_collection}' does not exist."
        )
    scope = _replacement_scope(metadata)
    collections = list(dict.fromkeys([primary_collection, UPLOAD_COLLECTION]))
    matches = []
    for collection in collections:
        points = _scroll_matching_points(client, collection, scope, with_vectors=False)
        matches.append({"collection": collection, "points": len(points)})
    return matches


def _prepare_chunks(metadata, content, pages):
    scope = _replacement_scope(metadata)
    document_id = str(uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"guide:{metadata['sha256']}:{scope['university_id']}:"
        f"{scope['category']}:{scope['degree_level']}",
    ))
    domains = sorted({
        domain
        for topic in scope["topics"]
        for domain in classify_topic(topic)[1]
    })
    university = UNIVERSITIES[scope["university_id"]]
    chunks = []
    for page in pages:
        for number, text in enumerate(split_text(page["text"]), start=1):
            chunk_id = str(uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"{document_id}:page:{page['page']}:chunk:{number}",
            ))
            chunks.append({
                "id": chunk_id,
                "text": (
                    f"University: {university}\n"
                    f"Degree level: {metadata['degree_level']}\n"
                    f"Academic year: {metadata['academic_year']}\n"
                    f"Intake: {metadata['intake_scope']}\n"
                    f"Guideline category: {metadata['category_label']}\n\n{text}"
                ),
                "university": university,
                "university_id": scope["university_id"],
                "degree": metadata["degree_level"],
                "degree_level": metadata["degree_level"],
                "topic": scope["topics"][0],
                "replacement_topics": scope["topics"],
                "category": scope["category"],
                "category_label": metadata["category_label"],
                "academic_year": metadata["academic_year"],
                "intake_scope": metadata["intake_scope"],
                "domains": domains,
                "document_domains": domains,
                "taxonomy_version": TAXONOMY["version"],
                "status": "staging",
                "audience": "international",
                "source_document": metadata["filename"],
                "filename": metadata["filename"],
                "source_path": (
                    f"{university.replace(' ', '_')}/"
                    f"{metadata['degree_level'].replace(' ', '_')}/"
                    f"{scope['category']}/{metadata['filename']}"
                ),
                "source_hash": metadata["sha256"],
                "document_id": document_id,
                "page": page["page"],
                "chunk_number": number,
            })
    if not chunks:
        raise ValueError("No indexable text was extracted from the PDF.")
    return chunks


def _ensure_upload_collection(client, vector_size):
    if not client.collection_exists(UPLOAD_COLLECTION):
        client.create_collection(
            collection_name=UPLOAD_COLLECTION,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )
    else:
        configured_vectors = client.get_collection(UPLOAD_COLLECTION).config.params.vectors
        configured_size = getattr(configured_vectors, "size", None)
        if configured_size != vector_size:
            raise RuntimeError(
                f"The upload collection uses {configured_size} dimensions, but "
                f"{EMBEDDING_MODEL} produces {vector_size}. Refusing to write "
                "incompatible vectors."
            )
    payload_schema = client.get_collection(UPLOAD_COLLECTION).payload_schema or {}
    for field in ("document_id", "status", "audience", "domains", "source_key"):
        if field not in payload_schema:
            client.create_payload_index(
                collection_name=UPLOAD_COLLECTION,
                field_name=field,
                field_schema=models.PayloadSchemaType.KEYWORD,
                wait=True,
            )


def _verify_staged_document(client, chunks, status):
    document_id = chunks[0]["document_id"]
    filter_by_document = models.Filter(must=[
        models.FieldCondition(
            key="document_id",
            match=models.MatchValue(value=document_id),
        ),
    ])
    points = []
    offset = None
    while True:
        batch, offset = client.scroll(
            collection_name=UPLOAD_COLLECTION,
            scroll_filter=filter_by_document,
            limit=128,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        points.extend(batch)
        if offset is None:
            break
    return (
        {str(point.id) for point in points} == {chunk["id"] for chunk in chunks}
        and all((point.payload or {}).get("status") == status for point in points)
        and all((point.payload or {}).get("source_hash") == chunks[0]["source_hash"]
                for point in points)
    )


def _normalized_chunk_text(text):
    normalized = str(text or "").strip()
    if normalized.startswith(("University: ", "Source document: ")) and "\n\n" in normalized:
        normalized = normalized.split("\n\n", 1)[1]
    return re.sub(r"\s+", " ", normalized).casefold().strip()


def _chunk_content_hash(text):
    return hashlib.sha256(_normalized_chunk_text(text).encode("utf-8")).hexdigest()


def _canonical_source_filename(filename):
    source_name = Path(str(filename or "")).name
    path = Path(source_name)
    stem = re.sub(r"\s*\(\d+\)$", "", path.stem).strip()
    return _normalize(f"{stem}{path.suffix}")


def _source_filename_matches(payload, filename):
    target = _canonical_source_filename(filename)
    if not target:
        return False
    names = {
        _canonical_source_filename(payload.get(field))
        for field in ("source_document", "filename")
    }
    return target in names


def _exact_source_filename_matches(payload, filename):
    target = _normalize(Path(filename).name)
    if not target:
        return False
    names = {
        _normalize(Path(str(payload.get(field) or "")).name)
        for field in ("source_document", "filename")
    }
    return target in names


def _collect_source_points(client, collection, filename):
    if not client.collection_exists(collection):
        return []
    matching = []
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=collection,
            limit=128,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        matching.extend(
            point for point in points
            if _source_filename_matches(point.payload or {}, filename)
            and str((point.payload or {}).get("status", "active")).casefold()
            not in {"upload_failed", "replacement_failed"}
        )
        if offset is None:
            break
    if not matching:
        return []

    snapshots = []
    for start in range(0, len(matching), 128):
        snapshots.extend(client.retrieve(
            collection_name=collection,
            ids=[point.id for point in matching[start:start + 128]],
            with_payload=True,
            with_vectors=True,
        ))
    if {str(point.id) for point in snapshots} != {
        str(point.id) for point in matching
    }:
        raise RuntimeError(f"Could not back up every matching source point in {collection}.")
    return snapshots


def _assert_source_points_replaceable(points, filename):
    university_ids = {
        _legacy_university_id(point.payload or {})
        for point in points
    } - {None}
    if len(university_ids) > 1:
        raise ValueError(
            f"More than one university is associated with '{filename}' in Qdrant. "
            "The source match is ambiguous; no vectors were changed."
        )

    for point in points:
        payload = point.payload or {}
        status = str(payload.get("status") or "active").casefold()
        if status != "active":
            raise ValueError(
                f"'{filename}' has non-active Qdrant records. Resolve their review "
                "status before replacing this source."
            )
        review_status = str(payload.get("review_status") or "").casefold()
        if review_status and review_status not in {"approved", "active"}:
            raise ValueError(
                f"'{filename}' contains records with review status "
                f"'{review_status}'. They were not changed; complete the review "
                "workflow before replacing this source."
            )
        publication_status = str(payload.get("publication_status") or "").casefold()
        if publication_status and publication_status not in {
            "approved", "published", "active",
        }:
            raise ValueError(
                f"'{filename}' contains records that are not approved for publication. "
                "They were not changed."
            )


def _verify_point_ids(client, chunks, status):
    points = client.retrieve(
        collection_name=UPLOAD_COLLECTION,
        ids=[chunk["id"] for chunk in chunks],
        with_payload=True,
        with_vectors=False,
    )
    by_id = {str(point.id): point for point in points}
    return (
        set(by_id) == {chunk["id"] for chunk in chunks}
        and all(
            (by_id[chunk["id"]].payload or {}).get("status") == status
            and (by_id[chunk["id"]].payload or {}).get("chunk_hash")
            == chunk["chunk_hash"]
            for chunk in chunks
        )
    )


def _incremental_source_metadata(points):
    university_ids = {
        _legacy_university_id(point.payload or {})
        for point in points
    } - {None}
    university_id = next(iter(university_ids), "general")
    university = UNIVERSITIES.get(university_id, "General knowledge")

    degrees = {
        _legacy_degree(point.payload or {})
        for point in points
    } - {"All degree levels"}
    degree = next(iter(degrees)) if len(degrees) == 1 else "Unspecified"

    topics = {
        _canonical_topic((point.payload or {}).get("topic"))
        for point in points
    } - {None}
    topic = next(iter(topics)) if len(topics) == 1 else "Other_Information"

    domains = set()
    for point in points:
        payload = point.payload or {}
        domains.update(payload.get("domains") or [])
        if not payload.get("domains"):
            domains.update(classify_topic(
                str(payload.get("topic") or "").replace(" ", "_")
            )[1])
    if not domains:
        domains.update(TAXONOMY["domains"])

    metadata = {
        "university_id": university_id,
        "university": university,
        "degree": degree,
        "degree_level": degree,
        "topic": topic,
        "domains": sorted(domains),
    }
    for field in ("category", "category_label", "academic_year", "intake_scope"):
        values = {
            (point.payload or {}).get(field)
            for point in points
            if (point.payload or {}).get(field) is not None
        }
        if len(values) == 1:
            metadata[field] = next(iter(values))
    for field in ("review_status", "publication_status"):
        values = {
            (point.payload or {}).get(field)
            for point in points
            if (point.payload or {}).get(field)
        }
        if len(values) == 1:
            metadata[field] = next(iter(values))
    return metadata


def _set_point_ids_status(client, point_ids, status):
    for start in range(0, len(point_ids), 128):
        batch = point_ids[start:start + 128]
        if batch:
            client.set_payload(
                collection_name=UPLOAD_COLLECTION,
                payload={"status": status},
                points=models.PointIdsList(points=batch),
                wait=True,
            )


def upload_document_to_qdrant(filename, content, client, embedding_model,
                              primary_collection=None):
    """Incrementally sync a source file, leaving unrelated Qdrant records untouched."""
    digest = hashlib.sha256(content).hexdigest()
    pages = extract_document_pages(filename, content)
    clean_filename = Path(filename).name
    source_key = hashlib.sha256(
        _canonical_source_filename(clean_filename).encode("utf-8")
    ).hexdigest()
    document_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"randyll-source:{source_key}"))
    chunks = []
    occurrences = {}
    for page in pages:
        for number, text in enumerate(split_text(page["text"]), start=1):
            chunk_hash = _chunk_content_hash(text)
            occurrence = occurrences.get(chunk_hash, 0)
            occurrences[chunk_hash] = occurrence + 1
            chunks.append({
                "id": str(uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"{document_id}:chunk:{chunk_hash}:occurrence:{occurrence}",
                )),
                "text": f"Source document: {clean_filename}\n\n{text}",
                "university": "General knowledge",
                "university_id": "general",
                "degree": "Unspecified",
                "degree_level": "Unspecified",
                "topic": "Other_Information",
                "domains": sorted(TAXONOMY["domains"]),
                "document_domains": sorted(TAXONOMY["domains"]),
                "taxonomy_version": TAXONOMY["version"],
                "status": "staging",
                "audience": "international",
                "source_document": clean_filename,
                "filename": clean_filename,
                "source_path": f"User_Uploads/{clean_filename}",
                "source_hash": digest,
                "chunk_hash": chunk_hash,
                "source_key": source_key,
                "document_id": document_id,
                "page": page["page"],
                "chunk_number": number,
            })
    if not chunks:
        raise ValueError("No indexable text was extracted from the document.")

    primary_collection = primary_collection or primary_collection_name()
    source_points_by_collection = {}
    for collection in dict.fromkeys((primary_collection, UPLOAD_COLLECTION)):
        source_points = _collect_source_points(client, collection, clean_filename)
        _assert_source_points_replaceable(source_points, clean_filename)
        source_points_by_collection[collection] = source_points

    all_source_points = [
        point
        for points in source_points_by_collection.values()
        for point in points
    ]
    exact_source_points = {
        collection: [
            point for point in points
            if _exact_source_filename_matches(point.payload or {}, clean_filename)
        ]
        for collection, points in source_points_by_collection.items()
    }
    has_exact_source = any(exact_source_points.values())
    reference_points_by_collection = (
        exact_source_points if has_exact_source else source_points_by_collection
    )
    reference_points = [
        point
        for points in reference_points_by_collection.values()
        for point in points
    ]
    source_metadata = _incremental_source_metadata(reference_points)
    if all_source_points:
        if Path(clean_filename).suffix.lower() == ".pdf":
            inferred_year = _infer_year_for_incremental_sync(
                clean_filename,
                pages[0]["text"],
            )
            if inferred_year is not None:
                source_metadata["academic_year"] = inferred_year
        for chunk in chunks:
            chunk.update(source_metadata)
            chunk["document_domains"] = source_metadata["domains"]

    existing_counts = {}
    for collection, points in reference_points_by_collection.items():
        for point in points:
            chunk_hash = _chunk_content_hash((point.payload or {}).get("text", ""))
            existing_counts[chunk_hash] = existing_counts.get(chunk_hash, 0) + 1

    unchanged = []
    changed = []
    preserve_counts = {}
    for chunk in chunks:
        available = existing_counts.get(chunk["chunk_hash"], 0)
        if available:
            unchanged.append(chunk)
            existing_counts[chunk["chunk_hash"]] = available - 1
            preserve_counts[chunk["chunk_hash"]] = (
                preserve_counts.get(chunk["chunk_hash"], 0) + 1
            )
        else:
            changed.append(chunk)

    if all_source_points and not has_exact_source:
        unchanged = []
        changed = list(chunks)

    obsolete = {collection: [] for collection in source_points_by_collection}
    for collection, points in source_points_by_collection.items():
        reference_ids = {
            str(point.id)
            for point in reference_points_by_collection.get(collection, [])
        }
        for point in points:
            if str(point.id) not in reference_ids:
                obsolete[collection].append(point)
                continue
            payload = point.payload or {}
            chunk_hash = _chunk_content_hash(payload.get("text", ""))
            if preserve_counts.get(chunk_hash, 0):
                preserve_counts[chunk_hash] -= 1
            else:
                obsolete[collection].append(point)

    if not changed and not any(obsolete.values()):
        return {
            "filename": clean_filename,
            "chunks": len(chunks),
            "unchanged_chunks": len(unchanged),
            "updated_chunks": 0,
            "removed_chunks": 0,
            "already_active": bool(unchanged),
            "matched_source": bool(all_source_points),
        }

    vector_size = embedding_model.get_sentence_embedding_dimension()
    if vector_size is None:
        raise RuntimeError("The embedding model did not report its vector size.")
    _ensure_upload_collection(client, vector_size)
    staged = []
    try:
        for start in range(0, len(changed), BATCH_SIZE):
            batch = changed[start:start + BATCH_SIZE]
            vectors = embedding_model.encode(
                [chunk["text"] for chunk in batch],
                normalize_embeddings=True,
                show_progress_bar=False,
                batch_size=BATCH_SIZE,
            )
            points = [
                models.PointStruct(
                    id=chunk["id"],
                    vector=vector.tolist(),
                    payload={key: value for key, value in chunk.items() if key != "id"},
                )
                for chunk, vector in zip(batch, vectors)
            ]
            client.upsert(
                collection_name=UPLOAD_COLLECTION,
                points=points,
                wait=True,
            )
            staged.extend(batch)

        if staged and not _verify_point_ids(client, staged, "staging"):
            raise RuntimeError("Qdrant could not verify every changed document vector.")
        if staged:
            _set_point_ids_status(client, [chunk["id"] for chunk in staged], "active")
            if not _verify_point_ids(client, staged, "active"):
                raise RuntimeError("Qdrant could not verify the active changed vectors.")
    except Exception as error:
        if staged and client.collection_exists(UPLOAD_COLLECTION):
            try:
                _set_point_ids_status(client, [chunk["id"] for chunk in staged], "upload_failed")
            except Exception as status_error:
                raise RuntimeError(
                    f"Incremental upload failed ({error}) and new vectors could not "
                    f"be marked inactive ({status_error})."
                ) from error
        raise

    deleted_counts = {}
    try:
        for collection, points in obsolete.items():
            _delete_points(client, collection, points)
            deleted_counts[collection] = len(points)
    except Exception as error:
        restore_errors = []
        for collection, points in obsolete.items():
            try:
                _restore_points(client, collection, points)
            except Exception as restore_error:
                restore_errors.append(f"{collection}: {restore_error}")
        if staged:
            try:
                _set_point_ids_status(
                    client,
                    [chunk["id"] for chunk in staged],
                    "replacement_failed",
                )
            except Exception as status_error:
                restore_errors.append(f"new vectors: {status_error}")
        detail = f"Incremental update failed; old vectors were restored where possible: {error}"
        if restore_errors:
            detail += " Restore errors: " + "; ".join(restore_errors)
        raise RuntimeError(detail) from error

    return {
        "filename": clean_filename,
        "chunks": len(chunks),
        "unchanged_chunks": len(unchanged),
        "updated_chunks": len(changed),
        "removed_chunks": sum(deleted_counts.values()),
        "deleted_by_collection": deleted_counts,
        "already_active": False,
        "matched_source": bool(all_source_points),
    }


def _change_document_status(client, document_id, status):
    client.set_payload(
        collection_name=UPLOAD_COLLECTION,
        payload={"status": status},
        points=models.Filter(must=[
            models.FieldCondition(
                key="document_id",
                match=models.MatchValue(value=document_id),
            ),
        ]),
        wait=True,
    )


def _delete_points(client, collection, points):
    if not points:
        return
    for start in range(0, len(points), 128):
        ids = [point.id for point in points[start:start + 128]]
        if ids:
            client.delete(
                collection_name=collection,
                points_selector=models.PointIdsList(points=ids),
                wait=True,
            )
    remaining = client.retrieve(
        collection_name=collection,
        ids=[point.id for point in points],
        with_payload=False,
        with_vectors=False,
    )
    if remaining:
        raise RuntimeError(
            f"Could not verify removal of old vectors from {collection}."
        )


def _restore_points(client, collection, points):
    for start in range(0, len(points), 128):
        batch = points[start:start + 128]
        client.upsert(
            collection_name=collection,
            points=[
                models.PointStruct(
                    id=point.id,
                    vector=point.vector,
                    payload=point.payload or {},
                )
                for point in batch
            ],
            wait=True,
        )


def replace_guide_in_qdrant(filename, content, metadata, client,
                            embedding_model, primary_collection=None):
    if hashlib.sha256(content).hexdigest() != metadata.get("sha256"):
        raise ValueError("The selected PDF changed after detection. Analyze it again.")
    primary_collection = primary_collection or primary_collection_name()
    if not client.collection_exists(primary_collection):
        raise ValueError(
            f"The configured knowledge collection '{primary_collection}' does not exist."
        )
    pages = extract_pages(filename, content)
    chunks = _prepare_chunks(metadata, content, pages)
    document_id = chunks[0]["document_id"]
    scope = _replacement_scope(metadata)
    target_collections = list(dict.fromkeys(
        [primary_collection, UPLOAD_COLLECTION]
    ))

    old_points = {
        collection: _scroll_matching_points(
            client, collection, scope, with_vectors=True
        )
        for collection in target_collections
        if client.collection_exists(collection)
    }
    if any(
        (point.payload or {}).get("document_id") == document_id
        and (point.payload or {}).get("status") == "active"
        for points in old_points.values()
        for point in points
    ):
        return {
            "filename": Path(filename).name,
            "chunks": len(chunks),
            "deleted_points": 0,
            "already_active": True,
            "deleted_by_collection": {},
        }

    vector_size = embedding_model.get_sentence_embedding_dimension()
    if vector_size is None:
        raise RuntimeError("The embedding model did not report its vector size.")
    _ensure_upload_collection(client, vector_size)

    try:
        for start in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[start:start + BATCH_SIZE]
            vectors = embedding_model.encode(
                [chunk["text"] for chunk in batch],
                normalize_embeddings=True,
                show_progress_bar=False,
                batch_size=BATCH_SIZE,
            )
            client.upsert(
                collection_name=UPLOAD_COLLECTION,
                points=[
                    models.PointStruct(
                        id=chunk["id"],
                        vector=vector.tolist(),
                        payload={key: value for key, value in chunk.items() if key != "id"},
                    )
                    for chunk, vector in zip(batch, vectors)
                ],
                wait=True,
            )
        if not _verify_staged_document(client, chunks, "staging"):
            raise RuntimeError(
                "Qdrant could not verify every new vector. "
                "Existing guide vectors were not deleted."
            )
    except Exception as error:
        if client.collection_exists(UPLOAD_COLLECTION):
            try:
                _change_document_status(client, document_id, "replacement_failed")
            except Exception as status_error:
                raise RuntimeError(
                    f"Staging failed ({error}) and the incomplete vectors could not "
                    f"be marked inactive ({status_error})."
                ) from error
        raise

    try:
        _change_document_status(client, document_id, "active")
        if not _verify_staged_document(client, chunks, "active"):
            raise RuntimeError(
                "Qdrant could not verify the new active vectors. "
                "Existing guide vectors were not deleted."
            )
    except Exception as error:
        try:
            _change_document_status(client, document_id, "replacement_failed")
        except Exception as status_error:
            raise RuntimeError(
                f"Activating the new vectors failed ({error}) and they could not "
                f"be marked inactive ({status_error})."
            ) from error
        raise

    deleted_by_collection = {}
    try:
        for collection, points in old_points.items():
            points = [
                point for point in points
                if str(point.id) not in {chunk["id"] for chunk in chunks}
            ]
            _delete_points(client, collection, points)
            deleted_by_collection[collection] = len(points)
    except Exception as error:
        restore_errors = []
        for collection, points in old_points.items():
            try:
                _restore_points(client, collection, points)
            except Exception as restore_error:
                restore_errors.append(f"{collection}: {restore_error}")
        try:
            _change_document_status(client, document_id, "replacement_failed")
        except Exception as status_error:
            restore_errors.append(f"new vectors: {status_error}")
        detail = f"Qdrant replacement failed; old vectors were restored where possible: {error}"
        if restore_errors:
            detail += " Restore errors: " + "; ".join(restore_errors)
        raise RuntimeError(detail) from error

    return {
        "filename": Path(filename).name,
        "chunks": len(chunks),
        "deleted_points": sum(deleted_by_collection.values()),
        "deleted_by_collection": deleted_by_collection,
        "already_active": False,
    }


def load_embedding_model():
    return SentenceTransformer(EMBEDDING_MODEL)
