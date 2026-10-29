
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def get_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "randyll_ai_db"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.environ["POSTGRES_PASSWORD"],
        row_factory=dict_row,
        connect_timeout=5,
    )


def get_universities():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, institution_type, website
                FROM university.universities
                WHERE active = TRUE
                ORDER BY name;
            """)
            return cur.fetchall()


def get_programs(university_name):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    u.name AS university,
                    p.program_name,
                    p.degree_level,
                    p.language_track,
                    p.admission_type,
                    p.transfer_entry_year,
                    c.campus_name,
                    s.document_name AS source_document, p.source_page,
                    p.academic_year, p.reviewed_at, p.review_notes, p.source_locator
                FROM university.academic_programs p
                JOIN university.universities u
                    ON p.university_id = u.id
                LEFT JOIN university.campuses c
                    ON p.campus_id = c.id
                JOIN knowledge.sources s ON p.source_id = s.id
                WHERE u.name ILIKE %s
                  AND p.active = TRUE
                  AND p.review_status = 'approved'
                ORDER BY p.program_name, p.admission_type;
            """, (university_name,))
            return cur.fetchall()


def get_tuition(university_name):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    u.name AS university,
                    t.field_of_study,
                    t.amount,
                    t.currency,
                    t.billing_period,
                    t.effective_year, t.degree_level, t.semester, t.notes,
                    s.document_name AS source_document, t.source_page,
                    t.reviewed_at, t.review_notes, t.source_locator
                FROM financial.tuition_rates t
                JOIN university.universities u
                    ON t.university_id = u.id
                JOIN knowledge.sources s ON t.source_id = s.id
                WHERE u.name ILIKE %s
                  AND t.review_status = 'approved'
                ORDER BY t.effective_year DESC,
                         t.field_of_study;
            """, (university_name,))
            return cur.fetchall()


def get_intakes(university_name):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    i.academic_year,
                    i.semester,
                    i.intake_round,
                    i.application_start
                        AT TIME ZONE 'Asia/Seoul'
                        AS application_start_kst,
                    i.application_deadline
                        AT TIME ZONE 'Asia/Seoul'
                        AS application_deadline_kst,
                    i.status, i.degree_level, i.notes,
                    s.document_name AS source_document, i.source_page,
                    i.reviewed_at, i.review_notes
                FROM admissions.admission_intakes i
                JOIN university.universities u
                    ON i.university_id = u.id
                JOIN knowledge.sources s ON i.source_id = s.id
                WHERE u.name ILIKE %s
                  AND i.review_status = 'approved'
                ORDER BY i.academic_year,
                         i.semester,
                         i.intake_round;
            """, (university_name,))
            return cur.fetchall()


def get_general_intakes():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT g.program_category, g.degree_scope, g.intake_month,
                       g.season, g.application_start_month, g.application_end_month,
                       g.application_year_offset, g.application_timing_text,
                       g.scope_notes, g.source_pages, g.reviewed_at, g.review_notes,
                       s.document_name AS source_document
                FROM admissions.general_intake_guidance g
                JOIN knowledge.sources s ON g.source_id = s.id
                WHERE g.review_status = 'approved'
                ORDER BY g.program_category, g.intake_month
            """)
            return cur.fetchall()


def get_agency_services(provider_name="Randyll Overseas"):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT a.provider_name, a.service_name, a.description,
                       a.scope_notes, a.source_page, a.reviewed_at, a.review_notes,
                       s.document_name AS source_document
                FROM agency.services a
                JOIN knowledge.sources s ON a.source_id = s.id
                WHERE a.provider_name = %s AND a.review_status = 'approved'
                ORDER BY a.id
            """, (provider_name,))
            return cur.fetchall()


def has_pending_agency_services(provider_name="Randyll Overseas"):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM agency.services
                    WHERE provider_name = %s AND review_status = 'pending'
                ) AS pending
            """, (provider_name,))
            return cur.fetchone()["pending"]
