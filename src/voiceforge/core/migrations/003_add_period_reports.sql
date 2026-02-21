-- Block 11.7 migration 3: period_reports.
CREATE TABLE IF NOT EXISTS period_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period_from TEXT NOT NULL,
    period_to TEXT NOT NULL,
    report_text TEXT NOT NULL,
    created_at TEXT NOT NULL
);
UPDATE schema_version SET version = 3 WHERE version < 3;
