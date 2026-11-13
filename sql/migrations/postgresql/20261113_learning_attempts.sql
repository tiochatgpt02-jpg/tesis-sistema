CREATE TABLE IF NOT EXISTS learning_attempts (
    id UUID PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id),
    topic_id BIGINT NOT NULL REFERENCES topics(id),
    kind TEXT NOT NULL CHECK (kind IN ('practice', 'exam')),
    scope TEXT NOT NULL,
    assessment_id BIGINT REFERENCES assessment(id),
    questions JSONB NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    submitted_at TIMESTAMPTZ,
    result JSONB
);
CREATE INDEX IF NOT EXISTS learning_attempts_student_scope
    ON learning_attempts(student_id, kind, scope);

CREATE TABLE IF NOT EXISTS exam_permissions (
    student_id BIGINT NOT NULL REFERENCES students(id),
    assessment_id BIGINT NOT NULL REFERENCES assessment(id),
    allowed_attempts INTEGER NOT NULL DEFAULT 1 CHECK (allowed_attempts > 0),
    reopened_by BIGINT REFERENCES users(id),
    reopened_at TIMESTAMPTZ,
    PRIMARY KEY (student_id, assessment_id)
);

CREATE TABLE IF NOT EXISTS prepared_practices (
    scope TEXT PRIMARY KEY,
    fingerprint TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stored_files (
    path TEXT PRIMARY KEY,
    content BYTEA NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (octet_length(content) <= 20971520)
);

CREATE TABLE IF NOT EXISTS grading_policy (
    id INTEGER PRIMARY KEY CHECK (id=1),
    practice_weight INTEGER NOT NULL CHECK (practice_weight > 0),
    exam_weight INTEGER NOT NULL CHECK (exam_weight > practice_weight),
    CHECK (practice_weight + exam_weight = 100)
);
