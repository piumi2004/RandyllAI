# Next tasks for the team: Improvements 1, 2 and 3

Hi team. This page is your to-do list for the next stretch of work. It covers the first three improvements in the technical strategy, and only those three:

1. **Organise the knowledge base by domain** (mostly built, content review still open)
2. **Use structured data alongside embeddings** (PostgreSQL, partly built)
3. **Redesign the document ingestion pipeline** (planned, not built yet)

Please hold off on hybrid search, reranking, AWS and the admin panel until these three are in good shape. Those later steps all depend on clean, trustworthy data. A better search engine can't fix a fee that was read off the wrong table row.

The longer background docs are still worth reading, and they're linked in each section. This page tells you what to actually *do*.

---

## A few ground rules first

These apply to every task below. They're the reason the chatbot can be trusted, so please don't treat them as optional.

- **Never invent or "fix" a fact.** If a fee, date or requirement looks wrong or unclear, write it down and flag it. Don't guess the right value.
- **Held content stays held until someone has checked it against the PDF.** "The parser produced output" is not the same as "this is correct".
- **Page numbers mean physical PDF pages.** The cover counts as page 1. These won't always match the page numbers printed inside a guide.
- **Don't hand-edit files in `data/knowledge_reviewed/`.** That folder is generated. Change the plan file or the code, then rebuild.
- **The `data/` folder isn't in Git.** If someone else needs a source file, share it directly, and tell us where it came from.
- **Run the tests before you rebuild the live index.** If a test fails, stop and sort it out, or ask.
- **Keep passwords and API keys out of every file you commit**, including docs and screenshots.

---

## Step 0: Check your setup works

Before starting anything, make sure you can rebuild what's there today. Run these from the project root in PowerShell, with Docker running:

```powershell
docker compose up -d
python backend/review_knowledge.py
.\.venv\Scripts\python.exe backend/index_knowledge.py --audit
.\.venv\Scripts\python.exe -m unittest test.test_knowledge_domains test.test_knowledge_review
```

What you should see:

- The builder prints **621 active** and **719 held** records.
- **22 tests pass.**

If your numbers differ, don't push on. Let us know first, because it probably means your copy of `data/` is different from ours.

`review_knowledge.py` needs PyMuPDF. On the main workstation it runs with the system Python, while indexing and tests use `.venv`. If PyMuPDF is missing, install it with `python -m pip install pymupdf`.

---

## Improvement 1: Finish the knowledge review

### What's already done

The project owner has already done the hard groundwork here, so you're picking up a working system:

- There's now a shared list of **eight domains** (education, universities, finances, culture & life, visas, employment, accommodation, applications) in `backend/domain_taxonomy.json`. Every topic maps to one or more of them.
- The loader no longer mislabels everything as "Randyll Semantic Knowledge", and the curated files are preferred properly again.
- The four "Unverified_" groups have been identified. They're **Yeungnam University College, Gachon University and Kongju National University** (Kongju has two guides). The Korean language course is now correctly marked as Ajou's non-degree programme.
- All 78 flagged files have a written recommendation in [flagged-knowledge-review.md](flagged-knowledge-review.md), and each one has an entry in `REVIEW_LEDGER.json`.
- A **review gate** is in place. Only records marked `active` and `international` can reach the chatbot. Everything else is held back but kept for tracing.
- Indexing now builds a **fresh collection**, checks every record, and only then switches the live alias over. If something goes wrong, the old collection is still there.
- Three Hannam items are fully done as worked examples: **R003** (graduate programme tables), **R004** and **R005** (undergraduate GPA table, appendices and forms).

So the machinery is finished. What's left is careful content work.

### How one review pass works

Every content fix follows the same loop. Use the finished Hannam entries in `backend/knowledge_review_sections.json` as your examples.

1. **Pick a ledger item** (say R056). Read its recommendation in `flagged-knowledge-review.md`.
2. **Open the original PDF** at the physical page it refers to. Work out exactly which section or table you need.
3. **Add a section plan** to `backend/knowledge_review_sections.json`. A simple one looks like this:

   ```json
   {
     "source": "Undergraduate.pdf",
     "page": 6,
     "topic": "Contact_Information",
     "region": [0, 0.05, 1, 0.69],
     "scope": "2027 spring international admission guide; retain the degree scope and all stated exceptions. Local source, not a current-policy certification."
   }
   ```

   - `region` is the part of the page to read, as fractions of width and height: `[left, top, right, bottom]`.
   - `topic` must be a topic that already exists in the taxonomy.
   - `scope` tells the chatbot what this passage applies to (year, intake, degree, applicant type).
   - For tables, add `"table": 0` (the table's number on that page). If the header row didn't extract cleanly, also add `"headers": [...]`.
   - If the table is too damaged to extract automatically, type the rows in yourself as `"headers"` plus `"checked_rows"`. Check every cell against the rendered page. Hannam's page 5 is the example to copy.
4. **Rebuild and read what came out.** Run `python backend/review_knowledge.py`, then open the generated file under `data/knowledge_reviewed/<University>/<Degree>/Reviewed/`. Compare it line by line with the PDF. Check the amounts, dates, degree markers, currency, footnotes and exceptions.
5. **Mark the item done in the ledger.** Right now the "reconstructed" status is set in code near the end of `review_knowledge.py` (look for `required_pages`). Add your item and the pages it needs there, so the ledger only says "done" once all those pages exist. Leave a short, honest note about what you did and didn't cover.
6. **Run the tests.** If your fix changes something important (like a fee row or a held file), add a test case to `test/test_knowledge_review.py`.
7. **Rebuild the live index** with `.\.venv\Scripts\python.exe backend/index_knowledge.py`. It will refuse to switch over if anything doesn't match.

If the builder stops with "Source changed since review", **don't just regenerate the hash.** Someone has a different version of that PDF. Open it, check that your page and region still point at the right content, and only then update `backend/knowledge_review_source_hashes.json`.

### Your Improvement 1 tasks

Work through these roughly in this order. The first two are the most valuable for students.

| # | Task | Ledger items | What "done" looks like |
|---|---|---|---|
| 1.1 | **Rebuild the Kongju, Gachon and Yeungnam tables** that are still held: programmes, housing, scholarships, required documents, contacts | Yeungnam R012–R025, Gachon R026–R038, Kongju graduate R039–R055, Kongju undergraduate R056–R073 | Each row keeps its headings, degree, year and notes. Old flattened text stays held, so don't reactivate it just because the university name is now right. |
| 1.2 | **Split the mixed Hannam graduate and Tongmyong passages** into proper topics | R002, R010, R011 | Navigation and consent text is separated from real answers. Every kept passage has a specific topic. |
| 1.3 | **Check KIT, Kunjang and Woosuk by audience and language.** These guides mix domestic and international rules, and some text is machine translated. | R006, R008, R009, R077, R078 | International-applicant content is recovered and marked as such. Domestic-only rules stay held. Kunjang has useful foreigner sections, so please don't drop the whole guide. |
| 1.4 | **Sort out the Woosong flyers and brochure.** Keep dated, attributed facts; hold vague promo claims and rankings with no year or source. | R074–R076 | Every ranking that's kept names who ranked it, the year and the category. |
| 1.5 | **Find real sources for the missing subjects.** Employment has zero content, and "culture & life" is only health insurance right now. | — | Send us a short list of official sources (for example government pages on part-time work for D-2 students) **before** adding anything. Nothing gets written from memory. |
| 1.6 | **Fill in the university name list in `backend/rag.py`.** `UNIVERSITY_ALIASES` only knows 8 schools. Hannam, HUFS, Woosong, KIT, Woosuk, Kunjang, Jeonju and Kyungbuk are missing, so questions about them skip the university filter and can mix schools together. | — | Every folder in `data/knowledge_reviewed/` has an entry with sensible short names. Avoid ambiguous ones: "KNU" could be Kongju, Kyungpook or Kyungbuk. |

HUFS (R001) and Ajou (R007) are lower priority. Tackle them once the rest are moving.

**Improvement 1 is finished when** every ledger item has either a checked replacement or a clear written reason for staying held, the missing subjects have approved sources, all tests pass, and the live index has been rebuilt from the final snapshot. Don't call it done just because the active review queue is empty. Held content doesn't show up in that queue.

---

## Improvement 2: Get the structured data working

Background: [structured-data-review.md](structured-data-review.md).

### Where it stands

You already wrote the query code: `backend/db.py`, `backend/structured_retrieval.py`, the PostgreSQL bits in `rag.py`, and `test_postgres.py`. That's a good start. The problem is that nobody else can run it yet:

- The tables it expects (`university.universities`, `university.academic_programs`, `university.campuses`, `financial.tuition_rates`, `admissions.admission_intakes`) don't exist in the shared setup, and there's no schema file in the repo.
- The `psycopg` driver isn't in `.venv`.
- There is a spreadsheet, `data/structured/University Programs and Fees DATABASE (1).xlsx`. It has a sheet each for 11 universities with majors, teaching language, degree type, tuition and dorm prices. But it has **no source page, no academic year, no "per semester or per year", and no date checked.** The LKR columns come from fixed exchange rates on the Parameters sheet. They're useful for a quick estimate, but they aren't facts from a university.

### Your Improvement 2 tasks

| # | Task | What "done" looks like |
|---|---|---|
| 2.1 | **Tell us where your database came from.** Send the schema and data export (or the scripts), the PostgreSQL version, and whether the spreadsheet was your source. Leave passwords out. | We can see what you built before anyone rebuilds it. |
| 2.2 | **Commit the schema as a SQL file** (for example `db/schema.sql`) that creates the tables `db.py` uses, plus setup steps in the README. | A fresh `docker compose up -d`, then running your file, gives working tables. |
| 2.3 | **Add the missing "where did this come from" fields** to programme, tuition and intake records: source document, physical page, academic year, intake, billing period (semester/year/one-off), date checked and who checked it. | Every fee in the database can be traced back to a PDF page. |
| 2.4 | **Write an import script** from the spreadsheet (or your export) into the database. Keep KRW as the stored value. Treat LKR/USD as calculated conversions with a dated exchange rate, not as stored facts. | Running it twice doesn't create duplicates. Bad rows are reported, not silently dropped. |
| 2.5 | **Spot-check 30 or so records against the PDFs**, spread across universities. Write down what matched and what didn't. | Mistakes found are fixed or flagged, and the results are recorded. |
| 2.6 | **Make the lookup smarter:** use the same university aliases as task 1.6, allow more than one category per question (tuition *and* deadlines), filter by city, degree, language and budget, and convert fees to the same period before comparing. | The strategy's example works: "English-taught CS master's in Seoul under 10 million KRW a year" returns a correct, sourced answer, or honestly says none was found. |
| 2.7 | **Show sources for database facts** in the answer, not just for Qdrant passages. Let a database answer still work even if the vector search fails. | A student can see which PDF page a fee came from. |
| 2.8 | **Turn `test_postgres.py` into real tests** with assertions: correct amounts, empty results, multi-filter queries and source fields present. | The tests fail if a number is wrong. Printing output doesn't count as a test. |

Please do 2.1 first. There's no point rebuilding a design you already have.

**Improvement 2 is finished when** a fresh setup can be rebuilt from the repo, sample records match their PDFs, the multi-filter example works, fees are compared on the same time period, and structured answers show where they came from.

---

## Improvement 3: Build the ingestion pipeline

Full instructions: [document-ingestion-guide.md](document-ingestion-guide.md). Read it before starting. Here's the short version, as tasks.

Today we have pieces: `extract_pdfs.py` (plain text only, skips scanned pages), `index_documents.py` (an old test indexer, **don't use it for the live chatbot**), and `test_ocr.py` (a Docling trial on two files). The job is to turn those into one repeatable pipeline, so a new PDF can go from "just downloaded" to "checked and searchable" without hand-patching.

The tool choice is **Docling, with EasyOCR set explicitly to Korean and English** (`ko`, `en`). Build and test it locally first. AWS comes later.

| # | Task | What "done" looks like |
|---|---|---|
| 3.1 | **Build a small test set of 20–30 real pages:** English, Korean, mixed, real scans, multi-column, merged tables, forms and tables that carry on across pages. Include the finished Hannam pages (graduate p4–5, undergraduate p10–11, p16–19, p20). A reviewer writes down the expected text and table cells from the actual page. | A benchmark file listing each page, its hash and what the correct output is. |
| 3.2 | **Set up a separate environment** for Docling/EasyOCR so it can't break the working chatbot. Pin the versions and note your CPU/GPU. | Someone else can rebuild your environment from your notes. |
| 3.3 | **Register every source:** ID, filename, SHA-256 hash, university, document type, language, year/intake, URL if known, and date obtained. Write "unknown" rather than guessing. | Duplicates are spotted by hash, and broken PDFs are reported. |
| 3.4 | **Extract page by page.** Keep good native text, and only OCR pages that are scanned or unreadable. Every page ends up as extracted, blank, held or failed. | No page just disappears with a warning in the terminal. |
| 3.5 | **Keep tables intact:** rows, columns, headings, merged cells, footnotes and page numbers. Don't mix up a dash, a blank and a zero. | The Hannam benchmark tables come out matching the reviewed versions. |
| 3.6 | **Clean carefully.** Remove repeated headers, footers and navigation, but never a table heading or a reference date. Keep the original text next to any cleaned-up version. | Nothing meaningful gets removed as "noise". |
| 3.7 | **Feed approved output into the existing review package** through an adapter, reusing the active/international gate and the safe index switch. Unchecked output never goes live. | Held content can't reach the chatbot, and a failed build leaves the live index alone. |
| 3.8 | **Measure and report:** text accuracy for Korean and English, exact numbers and dates, table alignment, missing rows, time taken and how much manual fixing was needed. Report scanned and native pages separately. | A short `docs/ingestion-benchmark.md` with real numbers and known failures. |

**Improvement 3 is finished when** a fresh environment can run the benchmark from documented commands, every page is accounted for, all the critical fields that were released match the source exactly, and anything unresolved is still held. Docling successfully exporting Markdown doesn't count as finished.

---

## Who could take what

Here's a suggestion based on the strategy's roles. Shuffle it to fit the team.

- **Data engineering:** Improvement 3 (all of it), plus help with 1.1 for difficult tables.
- **Content and QA:** Improvement 1, tasks 1.1–1.5 (most of the reading-PDFs-carefully work).
- **Backend:** Improvement 2, plus task 1.6.
- **Everyone:** write tests for whatever you change.

Improvements 1 and 2 can run at the same time. Improvement 3 can start with the benchmark (3.1) straight away, since it reuses the Hannam work from Improvement 1.

---

## How to report back

Once a week, a short update is plenty:

1. What you finished, with ledger IDs or task numbers.
2. Test output and the active/held counts from the builder.
3. Anything you held back, and why.
4. Questions or anything that looked wrong in a source.

Saying "I'm not sure about this one" is always better than guessing. Thanks, all. This is the work that makes the chatbot worth trusting.
