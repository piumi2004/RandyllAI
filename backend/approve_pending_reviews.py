"""Record an explicit owner bulk-approval without altering source facts or holds.

Dry run by default. Requires --apply, reviewer and reason to change PostgreSQL.
Numeric extraction quality, missing fee units and source warnings are preserved.
"""
import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from psycopg import sql
from psycopg.types.json import Jsonb

from backend.db import get_connection

ROOT = Path(__file__).resolve().parents[1]


def review_snapshot(row):
    return json.loads(json.dumps(row, default=str))


def approve_pending(apply=False, reviewer=None, reason=None):
    if apply and (not reviewer or not reason or not reviewer.strip() or not reason.strip()):
        raise ValueError("An explicit reviewer and approval reason are required")
    batch = uuid.uuid4()
    report = {"batch_id": str(batch), "mode": "applied" if apply else "dry_run",
              "reviewer": reviewer, "reason": reason, "tables": {}, "qdrant_writes": 0,
              "extraction_quality_and_missing_scope_preserved": True}
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.table_schema,c.table_name,array_agg(c.column_name::text) AS columns
                FROM information_schema.columns c
                JOIN information_schema.tables t
                  ON t.table_schema=c.table_schema AND t.table_name=c.table_name
                WHERE t.table_type='BASE TABLE'
                  AND c.table_schema IN ('knowledge','university','financial','admissions','agency')
                GROUP BY c.table_schema,c.table_name
                HAVING bool_or(c.column_name='review_status')
                ORDER BY c.table_schema,c.table_name
            """)
            tables = cur.fetchall()
            if apply:
                cur.execute((ROOT / "db/004_review_events.sql").read_text(encoding="utf-8"))
            for table in tables:
                columns = set(table["columns"])
                if "id" not in columns:
                    raise ValueError("Review table has no stable ID; refusing bulk update")
                name = table["table_schema"] + "." + table["table_name"]
                identifier = sql.Identifier(table["table_schema"], table["table_name"])
                fields = [key for key in ("id", "source_id", "review_status", "reviewed_by", "reviewed_at",
                                          "review_notes", "extraction_status") if key in columns]
                selected = sql.SQL(",").join(map(sql.Identifier, fields))
                cur.execute(sql.SQL("SELECT {} FROM {} WHERE review_status='pending' ORDER BY id FOR UPDATE").format(selected, identifier))
                before = cur.fetchall()
                report["tables"][name] = len(before)
                if not apply or not before:
                    continue
                changes = [sql.SQL("review_status=%s")]
                params = ["approved"]
                if "reviewed_by" in columns:
                    changes.append(sql.SQL("reviewed_by=%s"))
                    params.append(reviewer)
                if "reviewed_at" in columns:
                    changes.append(sql.SQL("reviewed_at=now()"))
                if "review_notes" in columns:
                    changes.append(sql.SQL("review_notes=concat_ws(E'\\n',nullif(review_notes,''),%s::text)"))
                    params.append("Owner-directed bulk approval: " + reason +
                                  " Source extraction warnings, unknown scope and numeric eligibility are unchanged; no independent per-cell verification is asserted.")
                params.append([r["id"] for r in before])
                cur.execute(sql.SQL("UPDATE {} SET {} WHERE id=ANY(%s) AND review_status='pending' RETURNING {}").format(
                    identifier, sql.SQL(",").join(changes), selected), params)
                after = {row["id"]: row for row in cur.fetchall()}
                if len(after) != len(before):
                    raise RuntimeError("Review rows changed concurrently; approval rolled back")
                events = [(batch, name, old["id"], reviewer, reason, "owner_bulk_approval",
                           Jsonb(review_snapshot(old)), Jsonb(review_snapshot(after[old["id"]]))) for old in before]
                cur.executemany("""
                    INSERT INTO knowledge.review_events
                    (batch_id,table_name,record_id,actor,reason,approval_kind,before_review,after_review)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, events)
    report["total"] = sum(report["tables"].values())
    if apply:
        output = ROOT / "data/ingestion_staging/corpus"
        output.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = output / f"BULK_APPROVAL_{stamp}_{batch}.json"
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        report["audit_file"] = str(path)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--reviewer")
    parser.add_argument("--reason")
    args = parser.parse_args()
    print(json.dumps(approve_pending(args.apply, args.reviewer, args.reason), indent=2))


if __name__ == "__main__":
    main()
