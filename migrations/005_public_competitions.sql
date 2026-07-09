-- Sprint 5 - Concorsi Pubblici
-- I bandi e i documenti personali restano locali.
-- Nel database vengono salvati solo metadati, stati e collegamenti.

CREATE TABLE IF NOT EXISTS public_competitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT DEFAULT '',
    organization TEXT DEFAULT '',
    category TEXT DEFAULT 'Altro',
    location TEXT DEFAULT '',
    source_url TEXT DEFAULT '',
    positions_count INTEGER DEFAULT 0,
    contract_type TEXT DEFAULT '',
    competition_status TEXT DEFAULT 'monitorato',
    application_status TEXT DEFAULT 'da_valutare',
    published_at TEXT DEFAULT '',
    application_opens_at TEXT DEFAULT '',
    deadline_at TEXT DEFAULT '',
    written_exam_at TEXT DEFAULT '',
    oral_exam_at TEXT DEFAULT '',
    ranking_at TEXT DEFAULT '',
    requirements TEXT DEFAULT '',
    required_documents TEXT DEFAULT '[]',
    personal_notes TEXT DEFAULT '',
    is_archived INTEGER DEFAULT 0,
    created_at TEXT DEFAULT '',
    updated_at TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS competition_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competition_id INTEGER DEFAULT 0,
    document_id INTEGER DEFAULT 0,
    purpose TEXT DEFAULT '',
    is_required INTEGER DEFAULT 1,
    is_ready INTEGER DEFAULT 0,
    notes TEXT DEFAULT '',
    created_at TEXT DEFAULT '',
    updated_at TEXT DEFAULT ''
);
