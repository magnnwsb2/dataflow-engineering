-- NexaRetail schema v1: ephemeral PostgreSQL 16, approved SDD plan.
-- Execute within a transaction. No persistent infrastructure is provisioned.

CREATE TABLE IF NOT EXISTS dim_branch (
    branch_id VARCHAR(4) PRIMARY KEY,
    branch_name VARCHAR(100) NOT NULL,
    state CHAR(2) NOT NULL,
    CONSTRAINT ck_branch_id CHECK (branch_id ~ '^F[0-9]{3}$'),
    CONSTRAINT ck_branch_state CHECK (state ~ '^[A-Z]{2}$')
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_id VARCHAR(5) PRIMARY KEY,
    product_name VARCHAR(120) NOT NULL,
    category VARCHAR(60) NOT NULL,
    CONSTRAINT ck_product_id CHECK (product_id ~ '^P[0-9]{4}$')
);

CREATE TABLE IF NOT EXISTS pipeline_run (
    run_id TEXT PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL CHECK (status IN ('running', 'succeeded', 'failed')),
    input_count INTEGER NOT NULL DEFAULT 0 CHECK (input_count >= 0),
    accepted_count INTEGER NOT NULL DEFAULT 0 CHECK (accepted_count >= 0),
    invalid_count INTEGER NOT NULL DEFAULT 0 CHECK (invalid_count >= 0),
    duplicate_count INTEGER NOT NULL DEFAULT 0 CHECK (duplicate_count >= 0),
    conflict_count INTEGER NOT NULL DEFAULT 0 CHECK (conflict_count >= 0),
    CONSTRAINT ck_run_finished CHECK (
        (status = 'running' AND finished_at IS NULL)
        OR (status <> 'running' AND finished_at IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS fact_sale (
    branch_id VARCHAR(4) NOT NULL REFERENCES dim_branch(branch_id),
    sale_id VARCHAR(9) NOT NULL,
    product_id VARCHAR(5) NOT NULL REFERENCES dim_product(product_id),
    sale_date DATE NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity BETWEEN 1 AND 1000),
    unit_price NUMERIC(14,2) NOT NULL CHECK (unit_price > 0),
    total_amount NUMERIC(16,2) NOT NULL CHECK (total_amount > 0),
    PRIMARY KEY (branch_id, sale_id),
    CONSTRAINT ck_sale_id CHECK (sale_id ~ '^V[0-9]{8}$'),
    CONSTRAINT ck_sale_total CHECK (total_amount = quantity * unit_price)
);

CREATE TABLE IF NOT EXISTS rejected_row (
    run_id TEXT NOT NULL REFERENCES pipeline_run(run_id),
    source_file TEXT NOT NULL,
    source_row INTEGER NOT NULL CHECK (source_row >= 2),
    reason_code TEXT NOT NULL,
    source_fingerprint TEXT NOT NULL CHECK (source_fingerprint ~ '^[0-9a-f]{64}$'),
    PRIMARY KEY (run_id, source_file, source_row, reason_code)
);

CREATE INDEX IF NOT EXISTS idx_fact_sale_date ON fact_sale (sale_date);
CREATE INDEX IF NOT EXISTS idx_fact_sale_product ON fact_sale (product_id);
CREATE INDEX IF NOT EXISTS idx_rejected_row_reason ON rejected_row (reason_code);
