-- Preserve original source content separately from reviewed structured facts.
CREATE TABLE IF NOT EXISTS university.aliases (
    alias text PRIMARY KEY,
    university_id bigint NOT NULL REFERENCES university.universities(id)
);

CREATE TABLE IF NOT EXISTS knowledge.source_passages (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id bigint NOT NULL REFERENCES knowledge.sources(id),
    locator text NOT NULL,
    source_page integer CHECK (source_page > 0),
    university_id bigint REFERENCES university.universities(id),
    degree_scope text,
    content text NOT NULL,
    extraction_method text NOT NULL,
    quality_notes text,
    review_status text NOT NULL DEFAULT 'pending' CHECK (review_status IN ('pending','approved','held')),
    search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    UNIQUE (source_id, locator)
);
CREATE INDEX IF NOT EXISTS source_passages_search ON knowledge.source_passages USING gin(search_vector);
CREATE INDEX IF NOT EXISTS source_passages_university ON knowledge.source_passages(university_id);

CREATE TABLE IF NOT EXISTS knowledge.source_tables (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id bigint NOT NULL REFERENCES knowledge.sources(id),
    source_page integer,
    locator text NOT NULL,
    university_id bigint REFERENCES university.universities(id),
    cells jsonb NOT NULL,
    geometry jsonb,
    context text NOT NULL,
    extraction_method text NOT NULL,
    review_status text NOT NULL DEFAULT 'pending' CHECK (review_status IN ('pending','approved','held')),
    UNIQUE(source_id, locator)
);

CREATE TABLE IF NOT EXISTS knowledge.numeric_observations (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id bigint NOT NULL REFERENCES knowledge.sources(id),
    locator text NOT NULL,
    source_page integer,
    raw_value text NOT NULL,
    context text NOT NULL,
    kind text NOT NULL,
    review_status text NOT NULL DEFAULT 'pending' CHECK (review_status IN ('pending','approved','held')),
    UNIQUE(source_id, locator)
);

ALTER TABLE university.academic_programs ADD COLUMN IF NOT EXISTS source_locator text;
ALTER TABLE university.academic_programs ADD COLUMN IF NOT EXISTS record_key text;
ALTER TABLE university.academic_programs ADD COLUMN IF NOT EXISTS extraction_status text NOT NULL DEFAULT 'structured';
ALTER TABLE university.academic_programs ALTER COLUMN source_page DROP NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS programs_source_record ON university.academic_programs(source_id, record_key);

ALTER TABLE financial.tuition_rates ADD COLUMN IF NOT EXISTS source_locator text;
ALTER TABLE financial.tuition_rates ADD COLUMN IF NOT EXISTS record_key text;
ALTER TABLE financial.tuition_rates ADD COLUMN IF NOT EXISTS amount_max numeric(16,2);
ALTER TABLE financial.tuition_rates ADD COLUMN IF NOT EXISTS extraction_status text NOT NULL DEFAULT 'structured';
ALTER TABLE financial.tuition_rates ADD COLUMN IF NOT EXISTS is_estimate boolean NOT NULL DEFAULT false;
ALTER TABLE financial.tuition_rates ALTER COLUMN source_page DROP NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS tuition_source_record ON financial.tuition_rates(source_id, record_key);

CREATE TABLE IF NOT EXISTS financial.cost_items (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id bigint NOT NULL REFERENCES knowledge.sources(id),
    university_id bigint REFERENCES university.universities(id),
    program_id bigint REFERENCES university.academic_programs(id),
    record_key text NOT NULL,
    cost_type text NOT NULL,
    amount numeric(16,2) NOT NULL CHECK (amount >= 0),
    currency text NOT NULL,
    billing_period text NOT NULL DEFAULT 'unknown',
    effective_year integer,
    source_page integer,
    source_locator text NOT NULL,
    source_excerpt text NOT NULL,
    is_estimate boolean NOT NULL DEFAULT false,
    review_status text NOT NULL DEFAULT 'pending' CHECK (review_status IN ('pending','approved','held')),
    UNIQUE (source_id, record_key)
);
