"""Export editable review CSVs; apply only explicitly reviewed rows.

This tool never approves a row merely because extraction succeeded.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

from backend.db import get_connection

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/ingestion_staging/corpus"
EDITABLE = ("decision", "reviewer", "review_notes", "billing_period", "effective_year", "degree_level", "amount")


def signature(row):
    fields = ("id", "source_id", "source_locator", "source_page", "source_excerpt", "amount", "degree_level", "billing_period", "effective_year", "review_status")
    return hashlib.sha256(json.dumps({k: str(row.get(k)) for k in fields}, sort_keys=True).encode()).hexdigest()


def export_fees():
    OUT.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT t.*,u.name AS university,s.document_name AS source_document
                           FROM financial.tuition_rates t JOIN university.universities u ON u.id=t.university_id
                           JOIN knowledge.sources s ON s.id=t.source_id ORDER BY t.id""")
            rows = cur.fetchall()
    path = OUT / "TUITION_REVIEW.csv"
    if path.exists():
        raise ValueError(f"Review file already exists: {path}. Preserve your decisions before exporting again.")
    fields = ["id", "university", "field_of_study", "source_document", "source_page", "source_locator",
              "current_status", "signature", *EDITABLE]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({**{k: row.get(k) for k in fields if k not in EDITABLE},
                             "current_status": row["review_status"], "signature": signature(row),
                             "decision": "", "reviewer": "", "review_notes": "",
                             "billing_period": row["billing_period"], "effective_year": row["effective_year"],
                             "degree_level": row["degree_level"], "amount": str(row["amount"])})
    print(f"Exported {len(rows)} fee rows to {path}")


def apply_review(path):
    from backend.corpus_ingestion import parse_amount
    with path.open(encoding="utf-8-sig", newline="") as handle:
        decisions = [r for r in csv.DictReader(handle) if r.get("decision", "").strip()]
    if len({r["id"] for r in decisions}) != len(decisions):
        raise ValueError("Duplicate row IDs in review file")
    with get_connection() as conn:
        with conn.cursor() as cur:
            for row in decisions:
                decision = row["decision"].strip().lower()
                if decision not in ("approved", "held", "pending") or not row["reviewer"].strip() or not row["review_notes"].strip():
                    raise ValueError("Each decision requires approved/held/pending, a real reviewer and review notes")
                cur.execute("SELECT * FROM financial.tuition_rates WHERE id=%s FOR UPDATE", (int(row["id"]),))
                old = cur.fetchone()
                if not old or signature(old) != row["signature"]:
                    raise ValueError("Stale or incorrect review row; no changes committed")
                amount = parse_amount(row["amount"])
                if amount is None or row["billing_period"] not in ("semester", "year", "credit", "one_off", "unknown"):
                    raise ValueError("Invalid fee amount or billing period")
                year = int(row["effective_year"]) if row["effective_year"].strip() else None
                if year is not None and not 1900 <= year <= 2200:
                    raise ValueError("Invalid fee year")
                if not row["degree_level"].strip():
                    raise ValueError("Degree scope required")
                cur.execute("""
                    UPDATE financial.tuition_rates
                    SET review_status=%s,reviewed_by=%s,reviewed_at=now(),review_notes=%s,
                        billing_period=%s,effective_year=%s,degree_level=%s,amount=%s,
                        extraction_status=CASE WHEN %s='approved' THEN 'structured' ELSE extraction_status END
                    WHERE id=%s
                """, (decision, row["reviewer"].strip(), row["review_notes"].strip(), row["billing_period"],
                      year, row["degree_level"].strip(), amount, decision, int(row["id"])))
    print(f"Committed {len(decisions)} explicit review decisions. Qdrant unchanged.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--export", action="store_true")
    group.add_argument("--apply", type=Path)
    args = parser.parse_args()
    export_fees() if args.export else apply_review(args.apply)


if __name__ == "__main__":
    main()
