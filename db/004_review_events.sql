-- Review decisions are recorded in the same transaction as status changes.
CREATE TABLE IF NOT EXISTS knowledge.review_events (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    batch_id uuid NOT NULL,
    table_name text NOT NULL,
    record_id bigint NOT NULL,
    actor text NOT NULL,
    reason text NOT NULL,
    approval_kind text NOT NULL,
    before_review jsonb NOT NULL,
    after_review jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (batch_id, table_name, record_id)
);
