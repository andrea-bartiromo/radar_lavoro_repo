-- Sprint 3 - CV Manager
-- I file CV restano sul computer dell'utente.
-- Nel database vengono salvati solo percorso locale e metadati.

CREATE TABLE IF NOT EXISTS cv_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT DEFAULT '',
    description TEXT DEFAULT '',
    version TEXT DEFAULT '',
    category TEXT DEFAULT 'Generico',
    file_path TEXT DEFAULT '',
    file_format TEXT DEFAULT '',
    checksum TEXT DEFAULT '',
    created_at TEXT DEFAULT '',
    updated_at TEXT DEFAULT '',
    is_active INTEGER DEFAULT 1,
    is_default INTEGER DEFAULT 0,
    notes TEXT DEFAULT ''
);
