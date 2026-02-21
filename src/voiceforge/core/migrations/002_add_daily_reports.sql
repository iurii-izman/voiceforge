-- Block 11.7 migration 2: daily_reports.
CREATE TABLE IF NOT EXISTS daily_reports (
    date TEXT PRIMARY KEY,
    report_text TEXT,
    batch_id TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL
);
UPDATE schema_version SET version = 2 WHERE version < 2;
