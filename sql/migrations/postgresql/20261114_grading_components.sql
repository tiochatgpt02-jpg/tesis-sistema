CREATE TABLE IF NOT EXISTS grading_component_policy (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    homework INTEGER NOT NULL CHECK (homework BETWEEN 0 AND 100),
    participation INTEGER NOT NULL CHECK (participation BETWEEN 0 AND 100),
    book INTEGER NOT NULL CHECK (book BETWEEN 0 AND 100),
    practice_1 INTEGER NOT NULL CHECK (practice_1 BETWEEN 0 AND 100),
    practice_2 INTEGER NOT NULL CHECK (practice_2 BETWEEN 0 AND 100),
    exam INTEGER NOT NULL CHECK (exam BETWEEN 0 AND 100),
    CHECK (homework + participation + book + practice_1 + practice_2 + exam = 100),
    CHECK (exam > GREATEST(homework, participation, book, practice_1, practice_2))
);

INSERT INTO grading_component_policy (id,homework,participation,book,practice_1,practice_2,exam)
VALUES (1,10,10,10,10,10,50)
ON CONFLICT (id) DO NOTHING;

CREATE TABLE IF NOT EXISTS bimester_manual_grades (
    student_id BIGINT NOT NULL REFERENCES students(id),
    academic_year SMALLINT NOT NULL CHECK (academic_year BETWEEN 2000 AND 2100),
    period SMALLINT NOT NULL CHECK (period BETWEEN 1 AND 4),
    component TEXT NOT NULL CHECK (component IN ('homework','participation','book','practice_1','practice_2','exam')),
    score NUMERIC(4,2) NOT NULL CHECK (score BETWEEN 0 AND 20),
    updated_by BIGINT REFERENCES users(id),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (student_id,academic_year,period,component)
);
CREATE INDEX IF NOT EXISTS bimester_manual_grades_period ON bimester_manual_grades(academic_year,period);

CREATE TABLE IF NOT EXISTS bimester_component_sources (
    grade SMALLINT NOT NULL CHECK (grade IN (4,5,6)),
    academic_year SMALLINT NOT NULL CHECK (academic_year BETWEEN 2000 AND 2100),
    period SMALLINT NOT NULL CHECK (period BETWEEN 1 AND 4),
    component TEXT NOT NULL CHECK (component IN ('practice_1','practice_2','exam')),
    source_item TEXT NOT NULL,
    updated_by BIGINT REFERENCES users(id),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (grade,academic_year,period,component),
    UNIQUE (grade,academic_year,period,source_item),
    CHECK ((component IN ('practice_1','practice_2') AND source_item LIKE 'practice:%')
        OR (component = 'exam' AND source_item LIKE 'exam:%'))
);
