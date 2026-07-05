-- Sprint 4 - Archivio Documenti
-- I documenti personali restano sul computer dell'utente.
-- Nel database vengono salvati solo percorsi locali e metadati.

CREATE TABLE IF NOT EXISTS document_archive (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT DEFAULT '',
    description TEXT DEFAULT '',
    category TEXT DEFAULT 'Altro',
    file_path TEXT DEFAULT '',
    file_format TEXT DEFAULT '',
    checksum TEXT DEFAULT '',
    tags TEXT DEFAULT '[]',
    related_cv_id INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pronto',
    is_active INTEGER DEFAULT 1,
    expires_at TEXT DEFAULT '',
    created_at TEXT DEFAULT '',
    updated_at TEXT DEFAULT '',
    notes TEXT DEFAULT ''
);
