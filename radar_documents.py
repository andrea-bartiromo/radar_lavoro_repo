"""Archivio documenti locale per Radar Lavoro.

Il modulo gestisce metadati e percorsi locali dei documenti utili alle
candidature. I file restano sul computer dell'utente e non vengono salvati
nel database.
"""

import json
from datetime import datetime
from pathlib import Path


DOCUMENT_CATEGORIES = [
    "CV",
    "Lettera di presentazione",
    "Certificazione",
    "Categorie protette",
    "Portfolio",
    "Documento amministrativo",
    "Bando o concorso",
    "Altro",
]

DOCUMENT_STATUS_OPTIONS = {
    "pronto": "Pronto",
    "bozza": "Bozza",
    "da_aggiornare": "Da aggiornare",
    "archiviato": "Archiviato",
}

DOCUMENT_FORMAT_OPTIONS = ["PDF", "DOCX", "TXT", "PNG", "JPG", "ZIP", "LINK", "Altro"]
DEFAULT_DOCUMENT_CATEGORY = "Altro"
DEFAULT_DOCUMENT_STATUS = "pronto"

DOCUMENT_TABLE_SQL = """
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
)
"""

DOCUMENT_COLUMNS = {
    "title": "TEXT DEFAULT ''",
    "description": "TEXT DEFAULT ''",
    "category": "TEXT DEFAULT 'Altro'",
    "file_path": "TEXT DEFAULT ''",
    "file_format": "TEXT DEFAULT ''",
    "checksum": "TEXT DEFAULT ''",
    "tags": "TEXT DEFAULT '[]'",
    "related_cv_id": "INTEGER DEFAULT 0",
    "status": "TEXT DEFAULT 'pronto'",
    "is_active": "INTEGER DEFAULT 1",
    "expires_at": "TEXT DEFAULT ''",
    "created_at": "TEXT DEFAULT ''",
    "updated_at": "TEXT DEFAULT ''",
    "notes": "TEXT DEFAULT ''",
}


def _now():
    return datetime.now().isoformat(timespec="minutes")


def _clean(value):
    return (value or "").strip()


def _load_json_list(value):
    try:
        parsed = json.loads(value or "[]")
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def _dump_json_list(values):
    return json.dumps(values or [], ensure_ascii=False)


def _split_lines(value):
    return [line.strip() for line in (value or "").splitlines() if line.strip()]


def _normalize_category(category):
    cleaned = _clean(category)
    return cleaned if cleaned in DOCUMENT_CATEGORIES else DEFAULT_DOCUMENT_CATEGORY


def _normalize_status(status):
    cleaned = _clean(status)
    return cleaned if cleaned in DOCUMENT_STATUS_OPTIONS else DEFAULT_DOCUMENT_STATUS


def _normalize_format(file_format, file_path):
    cleaned = _clean(file_format)
    if cleaned in DOCUMENT_FORMAT_OPTIONS:
        return cleaned
    suffix = Path(_clean(file_path)).suffix.lower().replace(".", "")
    if suffix == "pdf":
        return "PDF"
    if suffix == "docx":
        return "DOCX"
    if suffix == "txt":
        return "TXT"
    if suffix == "png":
        return "PNG"
    if suffix in {"jpg", "jpeg"}:
        return "JPG"
    if suffix == "zip":
        return "ZIP"
    if _clean(file_path).startswith(("http://", "https://")):
        return "LINK"
    return cleaned or "Altro"


def _checked(form, field_name, default=False):
    if hasattr(form, "getlist"):
        return field_name in form
    value = form.get(field_name, default)
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "on", "si", "yes"}


def _int_from_form(form, field_name):
    value = _clean(form.get(field_name))
    return int(value) if value.isdigit() else 0


def ensure_document_schema(conn, ensure_column):
    """Crea e aggiorna la tabella documenti senza perdere dati esistenti."""
    conn.execute(DOCUMENT_TABLE_SQL)
    for column_name, column_definition in DOCUMENT_COLUMNS.items():
        ensure_column(conn, "document_archive", column_name, column_definition)


def document_from_row(row):
    if row is None:
        return None
    document = dict(row)
    document["category"] = _normalize_category(document.get("category"))
    document["status"] = _normalize_status(document.get("status"))
    document["status_label"] = DOCUMENT_STATUS_OPTIONS[document["status"]]
    document["is_active"] = bool(document.get("is_active"))
    document["tags"] = _load_json_list(document.get("tags"))
    document["created_at_label"] = (document.get("created_at") or "").replace("T", " ")
    document["updated_at_label"] = (document.get("updated_at") or "").replace("T", " ")
    return document


def load_documents(conn, document_id=None):
    """Carica un documento specifico oppure tutto l'archivio ordinato."""
    if document_id is not None:
        row = conn.execute("SELECT * FROM document_archive WHERE id = ?", (document_id,)).fetchone()
        return document_from_row(row)
    rows = conn.execute(
        """
        SELECT *
          FROM document_archive
         ORDER BY is_active DESC, updated_at DESC, category ASC, id DESC
        """
    ).fetchall()
    return [document_from_row(row) for row in rows]


def save_document(conn, form, document_id=None):
    """Inserisce o aggiorna un documento salvando solo metadati e percorso."""
    now = _now()
    file_path = _clean(form.get("file_path"))
    values = {
        "title": _clean(form.get("title")) or "Documento senza titolo",
        "description": _clean(form.get("description")),
        "category": _normalize_category(form.get("category")),
        "file_path": file_path,
        "file_format": _normalize_format(form.get("file_format"), file_path),
        "checksum": _clean(form.get("checksum")),
        "tags": _dump_json_list(_split_lines(form.get("tags", ""))),
        "related_cv_id": _int_from_form(form, "related_cv_id"),
        "status": _normalize_status(form.get("status")),
        "is_active": 1 if _checked(form, "is_active", True) else 0,
        "expires_at": _clean(form.get("expires_at")),
        "updated_at": now,
        "notes": _clean(form.get("notes")),
    }

    if document_id:
        existing = load_documents(conn, document_id)
        if existing is None:
            document_id = None

    if document_id:
        assignments = ", ".join(f"{column} = ?" for column in values)
        conn.execute(
            f"UPDATE document_archive SET {assignments} WHERE id = ?",
            tuple(values.values()) + (document_id,),
        )
    else:
        values["created_at"] = now
        columns = ", ".join(values.keys())
        placeholders = ", ".join("?" for _ in values)
        cursor = conn.execute(
            f"INSERT INTO document_archive ({columns}) VALUES ({placeholders})",
            tuple(values.values()),
        )
        document_id = cursor.lastrowid
    return document_id


def delete_document(conn, document_id):
    """Elimina solo il record dall'archivio, mai il file locale."""
    document = load_documents(conn, document_id)
    if document is None:
        return False
    conn.execute("DELETE FROM document_archive WHERE id = ?", (document_id,))
    return True


def archive_document(conn, document_id):
    """Sposta un documento nello stato archiviato senza eliminarlo."""
    document = load_documents(conn, document_id)
    if document is None:
        return False
    conn.execute(
        """
        UPDATE document_archive
           SET status = 'archiviato', is_active = 0, updated_at = ?
         WHERE id = ?
        """,
        (_now(), document_id),
    )
    return True


def document_stats(documents):
    stats = {
        "totali": len(documents),
        "attivi": 0,
        "da_aggiornare": 0,
        "categorie": 0,
    }
    categories = set()
    for document in documents:
        if document.get("is_active"):
            stats["attivi"] += 1
        if document.get("status") == "da_aggiornare":
            stats["da_aggiornare"] += 1
        if document.get("category"):
            categories.add(document["category"])
    stats["categorie"] = len(categories)
    return stats
