# Project improvement guide

Use this guide to follow changes to the existing project and set up new improvements. We will add instructions here as the project owner identifies completed steps and we work through the next steps together.

## How to use this guide

Before making a change, read the relevant step and check whether it applies to your setup. Each step should explain what you need to do, why it matters, and how to check that it worked.

When an existing step changes, update its instructions here so the team can follow the current process. Explain what changed and whether anyone who completed the earlier version needs to take action. Keep the setup instructions in the README consistent with those changes.

For a new step, include any prerequisites, the files to edit, and the commands to run. State where to run commands and describe the expected result. If a step is still planned or has not been verified, say so clearly.

Write in plain, direct language. Explain unfamiliar terms when they first appear, and give enough context for someone else on the team to follow the instructions without needing the original conversation.

## Current intern tasks

The team's next tasks for Improvements 1, 2 and 3 are in [Next tasks for the team](intern-tasks-improvements-1-3.md). Please finish those before starting later improvements.

## Changes to completed steps

### Docker Compose now includes both databases

The original Compose file started only Qdrant 1.15.5. The application also queries PostgreSQL, but its database service was missing from the setup. The updated file defines Qdrant 1.20.0 and PostgreSQL 18.6, with persistent storage, local port bindings, log rotation, and a PostgreSQL readiness check.

If you already have Qdrant data, back it up and confirm the supported upgrade path before starting the newer image against that storage. Keep the same Compose project name and directory when reusing existing volumes. Changing the project name can make Docker create a separate set of volumes.

If PostgreSQL was set up elsewhere, obtain a schema and data export from that installation. Starting the new container does not copy that database automatically.

## New steps

### Step 1: Set up Qdrant and PostgreSQL

**Status:** Configuration implemented and database startup verified on 2026-10-27. PostgreSQL reported healthy and returned version 18.6 from a SQL query. Qdrant passed its readiness check and returned an empty collection list. Compose validation and whitespace checks passed. Importing the application schema and records remains a separate step.

#### Before you start

Start Docker Desktop with Linux containers enabled. Run the commands below in PowerShell from the project root, where `docker-compose.yml` is located. Make sure ports 6333 and 5432 are available.

#### Configure the database connection

Add these values to your existing `.env`. Preserve your LLM settings and replace the password placeholder with a strong password. Do not commit this file.

```dotenv
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=randyll_ai_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=replace_with_a_strong_local_password
```

The Python application runs on Windows and connects through localhost. Compose passes only the listed database settings to PostgreSQL. The local development setup uses the initial PostgreSQL administrator account; a restricted application role should be introduced before deployment.

The database name, user, and password initialize a new PostgreSQL volume. Editing these values later does not rename an existing database or change its stored password. Update an existing installation through PostgreSQL instead.

#### Validate and start the services

```powershell
docker compose config --quiet
docker compose up -d
docker compose ps
```

The validation command should finish without errors. PostgreSQL should eventually show `healthy`, and Qdrant should show `Up`. Qdrant has no container health check in this configuration; use its HTTP endpoint below to check readiness.

#### Check the result

```powershell
Invoke-RestMethod http://localhost:6333/readyz
Invoke-RestMethod http://localhost:6333/collections
docker compose exec -T postgres psql -U postgres -d randyll_ai_db -c "SELECT current_database(), version();"
```

Qdrant should return a successful readiness response and a collection list, which may be empty on a fresh installation. PostgreSQL should return the configured database name and server version. If you chose a different PostgreSQL user or database, replace `postgres` and `randyll_ai_db` in the command. This SQL check runs inside the container; it does not verify the Python application's password connection.

The Compose file creates an empty PostgreSQL application database. It does not yet create the `university`, `financial`, and `admissions` schemas used by the application. Once the schema and records have been imported, run `python test_postgres.py` from the project's Python environment to verify the application queries.

The local `.venv` did not have the `psycopg` driver installed during this verification, so the Python connection was not tested. Install the README dependencies, or install the driver directly in your activated environment with `python -m pip install "psycopg[binary]"`, before checking the application connection.

#### Storage and everyday commands

Qdrant stores its index in `qdrant_storage` and snapshots in `qdrant_snapshots`. PostgreSQL uses `postgres_storage`, mounted at `/var/lib/postgresql` for the PostgreSQL 18 image. These are Docker-managed volumes, separate from the source folder. A snapshot volume provides storage for snapshots; it does not schedule or create backups.

```powershell
# Read recent service logs.
docker compose logs --tail 100 qdrant postgres

# Stop the containers while keeping their data.
docker compose stop

# Start the services again.
docker compose up -d
```

Avoid `docker compose down -v` when you want to keep the data: it removes the Compose volumes. If port 5432 is already occupied, choose a free port in `POSTGRES_PORT`; the current Python connection code reads that same setting.

#### Version references

The selected versions follow the [Qdrant 1.20.0 release](https://github.com/qdrant/qdrant/releases/tag/v1.20.0) and [PostgreSQL version list](https://www.postgresql.org/support/versioning/). The volume layout and initialization behavior follow the [official PostgreSQL image documentation](https://hub.docker.com/_/postgres).

### Step 2: Organize the knowledge base by domain

**Status:** Domain retrieval and the initial approved content corrections are implemented. Content reconstruction remains in progress; this step is not fully finalized.

Read [Organizing the knowledge base by domain](knowledge-domains.md) for the original design, and [Applying the flagged-file review](knowledge-review-implementation.md) for the current flow, commands, results and remaining work. The [78-file review](flagged-knowledge-review.md) retains the original recommendations and justifications.

Completed:

- Corrected folder interpretation, curated-source precedence and source identities.
- Added eight domains, topic aliases, and the nine approved review topics.
- Corrected the placeholder institution groups and Ajou's non-degree course identity in the reviewed package.
- Reconstructed 298 source-section records, retaining table headings and scope.
- Enforced active status and international-applicant audience in indexing and both search paths.
- Added a review ledger for all 78 files and preserved original sources.
- Replaced in-place upserts with a fresh collection, complete payload verification and atomic alias promotion. Previous collections remain available.
- Passed 22 regression tests.
- Completed Hannam undergraduate review items R004 and R005: 41 GPA rows, dated appendices, complete form declarations and related verification passages. Five duplicate fragmented chunks are held.
- Completed Hannam review item R003: both graduate-program table pages are reconstructed, and degree-marker totals match the source.

The reviewed snapshot has 621 active records and 719 held original chunks. The live index has been rebuilt and verified against this snapshot. Some held chunks have replacements; others still need reconstruction or audience/language review. Do not mark the phase complete from an empty active-record review queue. Follow the remaining-work list in the implementation guide.

If you completed the earlier v3 setup, generate the reviewed package and run the full indexer as described in that guide. The application now uses `randyll_korea_knowledge_reviewed`. Single-file indexing is disabled to avoid stale chunks after corrections.

Missing-subject coverage and end-to-end answer-quality evaluation remain open. The PostgreSQL prerequisites recorded in Step 1 are unchanged.

### Step 3: Use structured data alongside embeddings

**Status:** Partially implemented; inspected on 2026-10-27. This is Improvement #2 in the technical strategy. The remaining Improvement #1 content reviews are left for the interns.

Read the [structured-data implementation review](structured-data-review.md) for the existing flow, completed code, verified local blockers, missing capabilities and requested intern deliverables.

The interns added PostgreSQL queries for universities, programs, tuition and intakes, basic keyword routing, and combined PostgreSQL/Qdrant context in the answer prompt. The local database lacks the expected application tables, and the project environment lacks `psycopg`. No schema or data export was found in the inspected workspace. Structured filtering, cost normalization, comparisons and record-level source references remain incomplete.

The next action is to obtain and inspect the interns' schema and data export before implementing replacements. No database restoration or application changes were made for this assessment, and this step is not marked complete.

### Step 4: Redesign the document ingestion pipeline

**Status:** Instructions prepared; implementation and benchmark verification pending. This is Improvement #3 in the technical strategy.

Follow the [document ingestion guide](document-ingestion-guide.md). Start with Docling and explicitly configured EasyOCR for Korean and English. Validate locally and retain AWS as the deployment direction.

The interns already have native PDF extraction, a separate test indexer and a two-document Docling OCR experiment. They have not connected those into the complete source-registration, validation, selective-OCR, cleaning, structure-aware chunking and review workflow. The recent reviewed-package corrections and safe index promotion should be reused and preserved.

The first deliverable is a 20–30-page benchmark with reviewed expected results. Then implement the documented stages and demonstrate that approved output is traceable, table relationships are correct, failed pages are accounted for and held content cannot enter retrieval. No OCR packages, pipeline changes or AWS resources were installed or deployed when preparing these instructions.

## Format for future steps



- **Status:** Planned, in progress, or completed. State separately whether the result has been verified.
- **Purpose:** Explain what this step improves and why it is needed.
- **Before you start:** List the required tools, configuration, and earlier steps.
- **Instructions:** Give the actions in order, with exact file paths and commands where useful. Use placeholders for secrets.
- **Check the result:** Describe how to verify the change and what success looks like. Record any checks that could not be run.
- **If you completed an earlier version:** Explain any follow-up action needed, or state that no action is required.
- **Known issues:** Include any unresolved limitations or troubleshooting relevant to this step.
