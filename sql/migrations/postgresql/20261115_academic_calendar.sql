CREATE TABLE IF NOT EXISTS school_year_bounds (
    academic_year SMALLINT PRIMARY KEY CHECK (academic_year BETWEEN 2000 AND 2100),
    date_from DATE NOT NULL,
    date_to DATE NOT NULL,
    source TEXT NOT NULL,
    CHECK (date_from <= date_to),
    CHECK (EXTRACT(YEAR FROM date_from)=academic_year AND EXTRACT(YEAR FROM date_to)=academic_year)
);
-- Annual dates supplied by the user; individual bimester boundaries remain unconfirmed.
INSERT INTO school_year_bounds(academic_year,date_from,date_to,source)
VALUES(2026,'2026-03-20','2026-12-18','Fechas anuales indicadas por el usuario el 15 de noviembre de 2026')
ON CONFLICT(academic_year) DO NOTHING;

CREATE TABLE IF NOT EXISTS academic_calendar (
    academic_year SMALLINT NOT NULL CHECK (academic_year BETWEEN 2000 AND 2100),
    period SMALLINT NOT NULL CHECK (period BETWEEN 1 AND 4),
    date_from DATE NOT NULL,
    date_to DATE NOT NULL,
    confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    updated_by BIGINT REFERENCES users(id),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (academic_year, period),
    CHECK (date_from <= date_to),
    CHECK (EXTRACT(YEAR FROM date_from) = academic_year AND EXTRACT(YEAR FROM date_to) = academic_year)
);
