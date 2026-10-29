"""Create the additive schema and import source-backed PDF facts.

Default is a dry run. --apply commits schema and records in one transaction.
Only the previously owner-approved intake section is approved automatically.
Agency statements remain pending human review.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

import pymupdf

from backend.db import get_connection

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/pdfs/Korea Student Admission Information - chatbot - Copy.pdf"
SOURCE_HASH = "7ee2b576c4f948269a27d8f00cd5e2f8452eaa0bc53ab981f1b37fcab3db582e"
SCOPE = (
    "User-supplied agency report; general guidance, not official university deadlines "
    "or current-policy certification. Availability varies by university and programme. "
    "Confirm the current official schedule. Admission does not guarantee visa approval."
)


def prepare_records():
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_HASH:
        raise ValueError("PDF changed: review the source before importing")
    with pymupdf.open(SOURCE) as pdf:
        pages = {n: pdf[n - 1].get_text(sort=True) for n in (2, 3, 4, 32)}
    intake_rows = []
    for month, season, start, end, offset in [
        (3, "Spring", 9, 11, -1), (9, "Fall", 4, 6, 0),
    ]:
        timing = ("Commonly September–November of the previous year" if month == 3
                  else "Commonly April–June of the intake year")
        intake_rows.append((f"degree_{month}", "Degree programmes",
                            "Associate, Bachelor's, Master's and Doctoral",
                            month, season, start, end, offset, timing,
                            [2, 3, 4], pages[2] + pages[3].split("2. D-4-1 Visa")[0] + pages[4]))
    for month, season in [(3, "Spring"), (6, "Summer"), (9, "Fall"), (12, "Winter")]:
        intake_rows.append((f"language_{month}", "Korean language programmes",
                            "Non-degree Korean language", month, season,
                            None, None, None,
                            "Institution-specific; applications may close several months before classes begin.",
                            [3, 4], pages[3].split("2. D-4-1 Visa", 1)[1] + pages[4]))
    service_text = re.sub(r"\n\s*\d+\s*$", "", pages[32])
    services = [re.sub(r"\s+", " ", item).strip()
                for item in service_text.split("\uf0b7")[1:]]
    if len(services) != 16:
        raise ValueError("Unexpected service list: inspect physical page 32")
    return intake_rows, services


def apply_records(conn, intake_rows, services):
    with conn.cursor() as cur:
        cur.execute((ROOT / "db/schema.sql").read_text(encoding="utf-8"))
        cur.execute("""
            INSERT INTO knowledge.sources (document_name, file_path, sha256, publisher, source_type)
            VALUES (%s,%s,%s,%s,%s) ON CONFLICT (sha256) DO NOTHING
        """, (SOURCE.name, SOURCE.relative_to(ROOT).as_posix(), SOURCE_HASH,
              "Randyll Overseas (user-supplied report)", "agency_report"))
        cur.execute("SELECT id FROM knowledge.sources WHERE sha256=%s", (SOURCE_HASH,))
        source_id = cur.fetchone()["id"]
        for key, category, degree, month, season, start, end, offset, timing, pages, excerpt in intake_rows:
            cur.execute("""
                INSERT INTO admissions.general_intake_guidance
                (source_id, record_key, program_category, degree_scope, intake_month, season,
                 application_start_month, application_end_month, application_year_offset,
                 application_timing_text, scope_notes, source_pages, source_excerpt,
                 review_status, reviewed_by, reviewed_at, review_notes)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                        'approved','Project owner',now(),%s)
                ON CONFLICT (source_id, record_key) DO NOTHING
            """, (source_id, key, category, degree, month, season, start, end, offset,
                  timing, SCOPE, pages, excerpt,
                  "Owner approved intake details in conversation; compared with rendered pages 2–4. "
                  "Approval concerns local-source transcription, not independently verified current policy."))
        for number, service in enumerate(services, 1):
            cur.execute("""
                INSERT INTO agency.services
                (provider_name, source_id, record_key, service_name, description,
                 source_page, source_excerpt, scope_notes, review_status, review_notes)
                VALUES ('Randyll Overseas',%s,%s,%s,%s,32,%s,%s,'pending',%s)
                ON CONFLICT (source_id, record_key) DO NOTHING
            """, (source_id, f"service_{number}", service, service, service,
                  "Agency's own service statement; not independent evidence of outcomes or a visa/admission guarantee.",
                  "Imported for review; service availability and terms require owner verification."))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Commit the additive schema and import")
    args = parser.parse_args()
    intakes, services = prepare_records()
    if args.apply:
        with get_connection() as conn:
            apply_records(conn, intakes, services)
    print(json.dumps({"mode": "committed" if args.apply else "dry_run",
                      "source": SOURCE.name, "approved_general_intake_rows": len(intakes),
                      "pending_service_rows": len(services),
                      "university_specific_records": 0, "qdrant_writes": 0}, indent=2))


if __name__ == "__main__":
    main()
