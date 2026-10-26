
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
                    c.campus_name
                FROM university.academic_programs p
                JOIN university.universities u
                    ON p.university_id = u.id
                JOIN university.campuses c
                    ON p.campus_id = c.id
                WHERE u.name ILIKE %s
                  AND p.active = TRUE
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
                    t.effective_year
                FROM financial.tuition_rates t
                JOIN university.universities u
                    ON t.university_id = u.id
                WHERE u.name ILIKE %s
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
                    i.status
                FROM admissions.admission_intakes i
                JOIN university.universities u
                    ON i.university_id = u.id
                WHERE u.name ILIKE %s
                ORDER BY i.academic_year,
                         i.semester,
                         i.intake_round;
            """, (university_name,))
            return cur.fetchall()
