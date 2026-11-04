-- Additive schema. No existing tables, collections or volumes are removed.
CREATE SCHEMA IF NOT EXISTS knowledge;
CREATE SCHEMA IF NOT EXISTS university;
CREATE SCHEMA IF NOT EXISTS financial;
CREATE SCHEMA IF NOT EXISTS admissions;
CREATE SCHEMA IF NOT EXISTS agency;

CREATE TABLE IF NOT EXISTS knowledge.sources (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_name text NOT NULL,
    file_path text NOT NULL,
    sha256 text NOT NULL UNIQUE CHECK (length(sha256) = 64),
    publisher text,
    source_type text NOT NULL,
    official_url text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS university.universities (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL UNIQUE,
    institution_type text,
    website text,
    active boolean NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS university.campuses (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    university_id bigint NOT NULL REFERENCES university.universities(id),
    campus_name text NOT NULL,
    city text,
    address text,
    UNIQUE (university_id, campus_name),
    UNIQUE (id, university_id)
);

CREATE TABLE IF NOT EXISTS university.academic_programs (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    university_id bigint NOT NULL REFERENCES university.universities(id),
    campus_id bigint,
    program_name text NOT NULL,
    degree_level text NOT NULL,
    language_track text,
    admission_type text,
    transfer_entry_year integer CHECK (transfer_entry_year > 0),
    academic_year integer,
    active boolean NOT NULL DEFAULT true,
    source_id bigint NOT NULL REFERENCES knowledge.sources(id),
    source_page integer NOT NULL CHECK (source_page > 0),
    source_excerpt text NOT NULL,
    review_status text NOT NULL DEFAULT 'pending' CHECK (review_status IN ('pending','approved','held')),
    reviewed_by text,
    reviewed_at timestamptz,
    review_notes text,
    FOREIGN KEY (campus_id, university_id) REFERENCES university.campuses(id, university_id),
    UNIQUE (id, university_id),
    CHECK (review_status <> 'approved' OR (reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS financial.tuition_rates (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    university_id bigint NOT NULL REFERENCES university.universities(id),
    program_id bigint,
    field_of_study text NOT NULL,
    degree_level text NOT NULL,
    amount numeric(16,2) NOT NULL CHECK (amount >= 0),
    currency text NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
    billing_period text NOT NULL CHECK (billing_period IN ('semester','year','credit','one_off','unknown')),
    effective_year integer,
    semester text,
    notes text,
    source_id bigint NOT NULL REFERENCES knowledge.sources(id),
    source_page integer NOT NULL CHECK (source_page > 0),
    source_excerpt text NOT NULL,
    review_status text NOT NULL DEFAULT 'pending' CHECK (review_status IN ('pending','approved','held')),
    reviewed_by text,
    reviewed_at timestamptz,
    review_notes text,
    FOREIGN KEY (program_id, university_id) REFERENCES university.academic_programs(id, university_id),
    CHECK (review_status <> 'approved' OR (reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS admissions.admission_intakes (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    university_id bigint NOT NULL REFERENCES university.universities(id),
    program_id bigint,
    degree_level text NOT NULL,
    academic_year integer NOT NULL,
    semester text NOT NULL,
    intake_round text NOT NULL,
    application_start timestamptz,
    application_deadline timestamptz,
    document_deadline timestamptz,
    status text NOT NULL DEFAULT 'unknown',
    notes text,
    source_id bigint NOT NULL REFERENCES knowledge.sources(id),
    source_page integer NOT NULL CHECK (source_page > 0),
    source_excerpt text NOT NULL,
    review_status text NOT NULL DEFAULT 'pending' CHECK (review_status IN ('pending','approved','held')),
    reviewed_by text,
    reviewed_at timestamptz,
    review_notes text,
    FOREIGN KEY (program_id, university_id) REFERENCES university.academic_programs(id, university_id),
    CHECK (application_deadline IS NULL OR application_start IS NULL OR application_deadline >= application_start),
    CHECK (review_status <> 'approved' OR (reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS admissions.general_intake_guidance (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id bigint NOT NULL REFERENCES knowledge.sources(id),
    record_key text NOT NULL,
    program_category text NOT NULL,
    degree_scope text NOT NULL,
    intake_month integer NOT NULL CHECK (intake_month BETWEEN 1 AND 12),
    season text NOT NULL,
    application_start_month integer CHECK (application_start_month BETWEEN 1 AND 12),
    application_end_month integer CHECK (application_end_month BETWEEN 1 AND 12),
    application_year_offset integer,
    application_timing_text text NOT NULL,
    scope_notes text NOT NULL,
    source_pages integer[] NOT NULL,
    source_excerpt text NOT NULL,
    review_status text NOT NULL DEFAULT 'pending' CHECK (review_status IN ('pending','approved','held')),
    reviewed_by text,
    reviewed_at timestamptz,
    review_notes text,
    UNIQUE (source_id, record_key),
    CHECK (review_status <> 'approved' OR (reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS agency.services (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    provider_name text NOT NULL,
    source_id bigint NOT NULL REFERENCES knowledge.sources(id),
    record_key text NOT NULL,
    service_name text NOT NULL,
    description text NOT NULL,
    source_page integer NOT NULL CHECK (source_page > 0),
    source_excerpt text NOT NULL,
    scope_notes text NOT NULL,
    review_status text NOT NULL DEFAULT 'pending' CHECK (review_status IN ('pending','approved','held')),
    reviewed_by text,
    reviewed_at timestamptz,
    review_notes text,
    UNIQUE (source_id, record_key),
    CHECK (review_status <> 'approved' OR (reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL))
);
