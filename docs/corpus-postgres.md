# Data-folder import and combined answers

The owner subsequently requested approval of all currently pending PostgreSQL
records. On 2026-10-29, 9,059 records were changed from pending to approved in
one transaction (batch `f66e05cb-2886-41a0-be09-26e3c8a1366d`). Per-record
before/after review metadata is in `knowledge.review_events`; the local report
is in `data/ingestion_staging/corpus/BULK_APPROVAL_20261029_102814_f66e05cb-2886-41a0-be09-26e3c8a1366d.json`.
This was owner-directed approval for use, not an assertion of independent
per-cell verification. Held records, source warnings, incomplete fee scope and
58 ambiguous PDF-geometry candidates were preserved. No pending rows remained
after this operation. Future imports still default to pending.

The initial-import descriptions below record the state before that decision.

The corpus importer reads the supplied files without changing originals or Qdrant.
It does not rebuild an index, switch an alias, remove collections or touch volumes.

```powershell
.\.venv\Scripts\python.exe -m backend.corpus_ingestion --extract
.\.venv\Scripts\python.exe -m backend.corpus_ingestion --apply
```

Extraction artifacts and source hashes are in `data/ingestion_staging/corpus/`.
Applying checks every source hash and imports in one PostgreSQL transaction.
Natural source keys prevent duplicate rows; existing review decisions are preserved.
NUL characters that PostgreSQL cannot represent are stored as visible literal
`\u0000` markers. The original files and raw JSONL extraction remain unchanged.

The initial import contains:

| Data | Records |
|---|---:|
| Original PDF physical pages | 423 across 25 PDFs |
| Source files, including the spreadsheet, OCR and derived topic files | 374 |
| Page/worksheet/OCR/topic passages | 2,220 |
| PDF tables and raw worksheet rows | 1,521 |
| Monetary and percentage observations with surrounding text | 680 |
| Spreadsheet programme records | 1,181 |
| Tuition candidates | 1,123 |
| Other original-currency cost records | 2,334 |

The 1,123 tuition records include 58 candidates from PDF table geometry.
Those candidates are marked `ambiguous` and excluded from automatic numeric
retrieval until inspected. All new records remain `pending`; import success
does not establish human review. Previously approved general intake guidance
and the sixteen owner-supplied service statements remain approved.

## View the records

Connect pgAdmin to `127.0.0.1:5433`, database `randyll_ai`.
The Docker-internal port can still appear as 5432 in SQL results.

```sql
SELECT * FROM knowledge.import_review_summary ORDER BY category, review_status;
SELECT * FROM financial.fee_review_queue ORDER BY university, degree_level, amount;
SELECT * FROM university.academic_programs ORDER BY university_id, program_name;
SELECT * FROM financial.cost_items ORDER BY university_id, cost_type, amount;
SELECT * FROM knowledge.source_passages ORDER BY source_id, source_page, id;
SELECT * FROM knowledge.source_tables ORDER BY source_id, source_page, id;
SELECT * FROM knowledge.numeric_observations ORDER BY source_id, source_page, id;
```

`knowledge.sources` retains the source filename, path and SHA-256. A worksheet
row is cited as a worksheet row, not as an invented PDF page. Existing OCR
Markdown has no dependable physical-page mapping and is cited by Markdown
line range. Two PDFs are image-only; the import retains all their physical-page
records and the existing OCR artifacts separately. Sparse pages, covers and
pages needing OCR/visual inspection appear in `EXTRACTION_REPORT.json`.
This import is not a claim that every scanned cell has been reconstructed.

## Review and fee comparisons

The spreadsheet often omits the fee year, billing period and original PDF page.
Unknown values stay NULL or `unknown`. LKR conversions and spreadsheet formulas
remain in raw rows; they are not silently imported as official original fees.
Program language flags are preserved without assuming that two "No" flags
mean a programme has no language of instruction.

An editable fee-review file is prepared at:

`data/ingestion_staging/corpus/TUITION_REVIEW.csv`

To create one in a fresh setup:

```powershell
.\.venv\Scripts\python.exe -m backend.review_structured --export
```

The exporter refuses to overwrite an existing review file. Compare each selected
fee with its source. Set `decision` to `approved`, `held` or `pending`; provide
the actual reviewer and review notes. Correct amount, degree scope, fee year
and billing period only from evidence. A reviewed amount with unknown period
can be listed with a warning but is not eligible for ranking.

```powershell
.\.venv\Scripts\python.exe -m backend.review_structured --apply data/ingestion_staging/corpus/TUITION_REVIEW.csv
```

Row signatures reject stale or mismatched decisions. Approval converts an
inspected geometry candidate to a structured fact; it does not certify future
policies. Inspect split tuition components carefully: a component is not the
total tuition. Correct totals and their scope in the reviewed record, documenting
the source and calculation. Never approve every candidate without inspection.

`financial.approved_tuition_comparison` shows fees with approved extraction,
known year and period, explicit degree scope, and no estimate/range ambiguity.
Comparison groups separate currency, billing period, fee year and degree. They
describe the listed fields/programmes, not a university-wide guaranteed price.
Unknown-period fees, estimates and unspecified graduate scopes are unranked.
No exchange conversion or semester-to-year multiplication is assumed.
Large catalogues are condensed to per-institution ranges so one institution's
hundreds of programme rows cannot crowd another out of a comparison.

## Runtime behaviour

`POSTGRES_ENABLED=true` enables PostgreSQL alongside the existing Qdrant v2
collection. The local host uses `127.0.0.1` to avoid a measured five-second
localhost/IPv6 connection delay in this environment.

The default is `STRUCTURED_SOURCE_MODE=approved`. Only approved new facts and
passages enter answers. The owner can explicitly choose a less restrictive
source-data mode by setting `STRUCTURED_SOURCE_MODE=labelled`: this allows
pending literal spreadsheet facts and extracted passages, labelled unreviewed,
while retaining review status and excluding held/ambiguous numeric records.
Do not enable that mode as a substitute for requested human approval.
Restart the app after changing environment settings.

The app resolves full university names and aliases, supports multiple named
universities, returns matching SQL facts plus PostgreSQL and Qdrant citations,
and sends both evidence sets to the answer model. Raw PDF text provides broader
coverage; exact comparisons come from numeric SQL columns. The application must
not derive a ranking from unrelated Qdrant or prose figures when SQL has no
comparable records. Programme, language, requested year, fee currency, billing
period and explicit budget constraints are supported. General programme searches
are limited to 60 listed rows; they are not a complete catalogue. Campus/city
filters and automatic general-purpose extraction of all academic/visa rules
into typed columns are not implemented; those rules remain source passages.

Document records do not automatically establish that a university's latest
policy, fee or intake is represented. Preserve source years and qualifiers.

## Checks

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s test -p test_corpus_ingestion.py
.\.venv\Scripts\python.exe -m unittest discover -s test -p test_structured_retrieval.py
```

`DATABASE_REPORT.json` records the verified import counts. The import was run
twice without duplicating data or changing existing service approvals. Real SQL
comparison checks used temporary fixtures in a transaction that was rolled back;
no synthetic comparison fees were left in the database.
