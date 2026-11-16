ALTER TABLE assessment ADD COLUMN IF NOT EXISTS kind TEXT NOT NULL DEFAULT 'exam';
DO $$ BEGIN
    ALTER TABLE assessment ADD CONSTRAINT assessment_kind_check CHECK (kind IN ('practice','exam'));
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
