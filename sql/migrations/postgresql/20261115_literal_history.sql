CREATE TABLE IF NOT EXISTS student_literal_history (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id),
    academic_year SMALLINT NOT NULL CHECK (academic_year BETWEEN 2000 AND 2100),
    period SMALLINT NOT NULL CHECK (period BETWEEN 1 AND 4),
    subject TEXT NOT NULL DEFAULT 'computacion',
    ratings JSONB NOT NULL CHECK (jsonb_typeof(ratings)='object'),
    final_rating TEXT NOT NULL CHECK (final_rating IN ('AD','A','B','C')),
    source_sha256 TEXT NOT NULL CHECK (length(source_sha256)=64),
    source_name TEXT NOT NULL,
    source_row INTEGER NOT NULL CHECK (source_row > 0),
    imported_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id,academic_year,period,subject)
);
CREATE INDEX IF NOT EXISTS student_literal_history_year_period ON student_literal_history(academic_year,period);
