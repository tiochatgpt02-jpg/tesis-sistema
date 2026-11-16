CREATE TABLE IF NOT EXISTS bimester_closures (
    grade SMALLINT NOT NULL CHECK (grade IN (4,5,6)),
    academic_year SMALLINT NOT NULL CHECK (academic_year BETWEEN 2000 AND 2100),
    period SMALLINT NOT NULL CHECK (period BETWEEN 1 AND 4),
    closed BOOLEAN NOT NULL DEFAULT FALSE,
    snapshot JSONB NOT NULL,
    closed_by BIGINT REFERENCES users(id),
    closed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(grade,academic_year,period)
);
CREATE TABLE IF NOT EXISTS bimester_closure_events (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    grade SMALLINT NOT NULL CHECK (grade IN (4,5,6)),
    academic_year SMALLINT NOT NULL CHECK (academic_year BETWEEN 2000 AND 2100),
    period SMALLINT NOT NULL CHECK (period BETWEEN 1 AND 4),
    action TEXT NOT NULL CHECK (action IN ('close','reopen')),
    reason TEXT NOT NULL CHECK (length(reason) BETWEEN 5 AND 500),
    snapshot JSONB,
    actor_id BIGINT REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS bimester_closure_events_scope ON bimester_closure_events(grade,academic_year,period);
