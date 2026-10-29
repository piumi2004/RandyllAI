# PostgreSQL setup and source review

The application uses PostgreSQL for approved structured facts and Qdrant for source passages.
The initial schema is in `db/schema.sql`. It adds tables without removing existing data.
The configured database comes from `.env`; never put a password in source files.

From the project root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m backend.setup_postgres
.\.venv\Scripts\python.exe -m backend.setup_postgres --apply
```

The first command validates the pinned PDF and reports a dry run. The second
creates the tables and imports records in one transaction. Running it again
does not duplicate the same source or overwrite existing review decisions.
The importer accepts this exact PDF version only; changed files require review.
It does not write to Qdrant or promote an index.

| Table | Purpose | Initial data |
|---|---|---|
| `knowledge.sources` | Source filename, SHA-256, publisher and source type | Supplied agency report |
| `university.universities` | Institution identity | Empty |
| `university.campuses` | Campus and city | Empty |
| `university.academic_programs` | Degree, teaching language and admission route | Empty |
| `financial.tuition_rates` | Original-currency amount, period, year and degree scope | Empty |
| `admissions.admission_intakes` | University-specific year, round and exact dates | Empty |
| `admissions.general_intake_guidance` | Month-level general guidance without invented exact dates | Six approved records, physical pages 2–4 |
| `agency.services` | Provider's own service statements and terms | Sixteen records, physical page 32; subsequently owner-approved |

The project owner approved the intake section in conversation. This approves
the local source transcription, not current immigration policy or a university's
official schedule. Degree intakes have month-level application windows; language
course deadlines remain unknown. No fabricated university, tuition or exact-date
records are inserted.

The owner subsequently supplied and approved the exact sixteen service statements
for chatbot use. Their approval is recorded in PostgreSQL. Inspect their text:

```sql
SELECT a.id, a.service_name, a.description, a.scope_notes,
       a.source_page, s.document_name, a.review_status
FROM agency.services a
JOIN knowledge.sources s ON s.id = a.source_id
ORDER BY a.id;
```

Compare each selected row with physical page 32 and confirm that the service is
actually offered under the stated terms. Record the real reviewer's name,
review time and decision for specific IDs. For example, in a parameterized
review tool, update `review_status`, `reviewed_by`, `reviewed_at` and
`review_notes` together. Do not bulk approve uninspected records.
An import request does not certify service availability, exam outcomes or visas.

Only approved records enter structured answers. Pending and held records remain
stored for review. Structured results include PDF page references, which the app
shows alongside Qdrant sources. General intake questions query general guidance;
named university questions do not substitute that guidance for exact schedules.

Enable the connection after schema setup:

```text
POSTGRES_ENABLED=true
```

Restart Streamlit after changing the setting. The app retains Qdrant retrieval.
PostgreSQL failure is logged and leaves Qdrant available; if Qdrant search fails
after an embedding succeeds, approved structured results can still answer.
Embedding failure still ends the request; full independent structured routing
is a separate improvement. Exact requested-year and degree filtering for future
university records remains to be implemented before loading multiple scopes.

Useful verification commands:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s test -p test_structured_retrieval.py
.\.venv\Scripts\python.exe -c "from backend.db import get_general_intakes, get_agency_services; print(len(get_general_intakes()), len(get_agency_services()))"
```

For more university data, register its source, then add the institution, campus
and program before adding linked tuition or intake records. Keep unknown values
NULL and new facts pending until checked. Preserve billing periods, academic
years, degree scope, source excerpts and physical PDF pages. Do not treat the
spreadsheet's exchange-rate estimates as official university fee amounts.

The data-folder corpus import and numeric comparison workflow are documented in
[Data-folder import and combined answers](corpus-postgres.md). Its new records
remain pending review; the initial empty-table descriptions above refer to the
earlier setup, not the subsequent corpus import.
