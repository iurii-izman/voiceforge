-- Action items in separate table for cross-session tracking and history --action-items. ADR-0002.
CREATE TABLE IF NOT EXISTS action_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    idx_in_analysis INTEGER NOT NULL,
    description TEXT NOT NULL,
    assignee TEXT,
    deadline TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
CREATE INDEX IF NOT EXISTS idx_action_items_session_id ON action_items(session_id);
UPDATE schema_version SET version = 5 WHERE version < 5;
