-- Add template to analyses (meeting template used for analyze). Block 7 improvement.
ALTER TABLE analyses ADD COLUMN template TEXT;
UPDATE schema_version SET version = 4 WHERE version < 4;
