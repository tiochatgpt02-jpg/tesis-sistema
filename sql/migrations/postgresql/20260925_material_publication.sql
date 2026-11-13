ALTER TABLE topics
    ADD COLUMN IF NOT EXISTS section VARCHAR(10),
    ADD COLUMN IF NOT EXISTS unit_number INTEGER,
    ADD COLUMN IF NOT EXISTS session_number INTEGER;

UPDATE topics
SET session_number = substring(title FROM '([0-9]+)')::INTEGER
WHERE session_number IS NULL
  AND title ~* '^Sesión[[:space:]]+[0-9]+';

UPDATE topics
SET unit_number = ((session_number - 1) / 4) + 1
WHERE unit_number IS NULL
  AND session_number BETWEEN 1 AND 32;

ALTER TABLE learning_materials
    ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'PUBLISHED';
ALTER TABLE learning_materials
    ALTER COLUMN status SET DEFAULT 'DRAFT';

ALTER TABLE topic_presentations
    ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'PUBLISHED';
ALTER TABLE topic_presentations
    ALTER COLUMN status SET DEFAULT 'DRAFT';

CREATE INDEX IF NOT EXISTS idx_topics_grade_section_unit_session
    ON topics (grade, section, unit_number, session_number);
CREATE INDEX IF NOT EXISTS idx_learning_materials_status_topic
    ON learning_materials (status, topic_id);
CREATE INDEX IF NOT EXISTS idx_topic_presentations_status_topic
    ON topic_presentations (status, topic_id);
