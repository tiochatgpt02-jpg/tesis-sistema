ALTER TABLE topics
    ADD COLUMN section VARCHAR(10) NULL,
    ADD COLUMN unit_number INT NULL,
    ADD COLUMN session_number INT NULL;

UPDATE topics
SET session_number = CAST(REGEXP_SUBSTR(title, '[0-9]+') AS UNSIGNED)
WHERE session_number IS NULL
  AND title REGEXP '^[[:space:]]*[Ss]esión[[:space:]]+[0-9]+';

UPDATE topics
SET unit_number = FLOOR((session_number - 1) / 4) + 1
WHERE unit_number IS NULL
  AND session_number BETWEEN 1 AND 32;

ALTER TABLE learning_materials
    ADD COLUMN status ENUM('DRAFT', 'PUBLISHED') NOT NULL DEFAULT 'PUBLISHED';
ALTER TABLE learning_materials
    ALTER COLUMN status SET DEFAULT 'DRAFT';

ALTER TABLE topic_presentations
    ADD COLUMN status ENUM('DRAFT', 'PUBLISHED') NOT NULL DEFAULT 'PUBLISHED';
ALTER TABLE topic_presentations
    ALTER COLUMN status SET DEFAULT 'DRAFT';

CREATE INDEX idx_topics_grade_section_unit_session
    ON topics (grade, section, unit_number, session_number);
CREATE INDEX idx_learning_materials_status_topic
    ON learning_materials (status, topic_id);
CREATE INDEX idx_topic_presentations_status_topic
    ON topic_presentations (status, topic_id);
