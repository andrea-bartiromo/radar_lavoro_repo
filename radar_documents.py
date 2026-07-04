"""Archivio documenti per Radar Lavoro.

Il modulo gestisce solo metadati e percorsi locali. I file restano sul PC
dell'utente e non vengono salvati nel repository o nel database.
"""

from datetime import date, datetime
from pathlib import Path


DOCUMENT_CATEGORIES = [
    "Curriculum",
    "Lettera di presentazione",
    "Certificazione",
    "Attestato",
    "Titolo di studio",
    "Portfolio",
    "Concorsi pubblici",
    "Documento personale",
    "Altro",
]

DOCUMENT_FORMAT_OPTIONS = ["PDF", "DOCX", "DOC", "PNG", "JPG", "TXT", "LINK", "Altro"]
DOCUMENT_STATUS_OPTIONS = ["attivo", "da aggiornare", "scaduto", "archiviato"]
DEFAULT_DOCUMENT_CATEGORY = "Altro"
DEFAULT_DOCUMENT_STATUS = "attivo"

DOCUMENT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS document_archive (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT DEFAULT '',
    category TEXT DEFAULT 'Altro',
    document_type TEXT DEFAULT '',
    file_path TEXT DEFAULT '',
    file_format TEXT DEFAULT '',
    issuer TEXT DEFAULT '',
    version TEXT DEFAULT '',
    tags TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    expires_at TEXT DEFAULT '',
    related_cv_id INTEGER,
    related_job_id INTEGER,
    is_favorite INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    status TEXT DEFAULT 'attivo',
    created_at TEXT DEFAULT '',
    updated_at TEXT DEFAULT ''
)
"""

DOCUMENT_COLUMNS = {
    "name": "TEXT DEFAULT ''",
    "category": "TEXT DEFAULT 'Altro'",
    "document_type": "TEXT DEFAULT ''",
    "file_path": "TEXT DEFAULT ''",
    "file_format": "TEXT DEFAULT ''",
    "issuer": "TEXT DEFAULT ''",
    "version": "TEXT DEFAULT ''",
    "tags": "TEXT DEFAULT ''",
    "notes": "TEXT DEFAULT ''",
    "expires_at": "TEXT DEFAULT ''",
    "related_cv_id": "INTEGER",
    "related_job_id": "INTEGER",
    "is_favorite": "INTEGER DEFAULT 0",
    "is_active": "INTEGER DEFAULT 1",
    "status": "TEXT DEFAULT 'attivo'",
    "created_at": "TEXT DEFAULT ''",
    "updated_at": "TEXT DEFAULT ''",
}

DEFAULT_DOCUMENTS = [
    {
        "name": "CV Generico",
        "category": "Curriculum",
        "document_type": "Curriculum vitae",
        "file_format": "PDF",
        "file_path": "Da impostare: percorso locale del CV generico",
        "tags": "cv, comunicazione, digitale, generico",
        "notes": "Documento locale collegabile al CV Manager.",
        "is_favorite": 1,
    },
    {
        "name": "CV Web Developer",
        "category": "Curriculum",
        "document_type": "Curriculum vitae",
        "file_format": "DOCX",
        "file_path": "Da impostare: percorso locale del CV Web Developer",
        "tags": "cv, web developer, python, laravel, mysql",
        "notes": "Documento locale collegabile al CV Manager.",
        "is_favorite": 0,
    },
    {
        "name": "Lettera di presentazione generica",
        "category": "Lettera di presentazione",
        "document_type": "Lettera motivazionale",
        "file_format": "Altro",
        "file_path": "Da creare",
        "tags": "lettera, candidatura, generica",
        "notes": "Placeholder per future lettere personalizzate.",
        "is_favorite": 0,
    },
    {
        "name": "Cartella certificazioni",
        "category": "Certificazione",
        "document_type": "Raccolta certificazioni",
        "file_format": "Altro",
        "file_path": "Da impostare: cartella locale certificazioni",
        "tags": "certificazioni, attestati, formazione",
        "notes": "Raccoglie certificazioni e attestati utili alle candidature.",
        "is_favorite": 0,
    },
    {
        "name": "Documenti concorsi pubblici",
        "category": "Concorsi pubblici",
        "document_type": "Checklist documentale",
        "file_format": "Altro",
        "file_path": "Da impostare: cartella locale concorsi",
        "tags": "concorsi, pa, documenti, checklist",
        "notes": "Base per lo Sprint Concorsi pubblici.",
        "is_favorite": 0,
    },
]


def _now():
    return datetime.now().isoformat(timespec="minutes")


def _clean(value):
    return (value or "").strip()


def _checked(form, field_name, default=False):
    if hasattr(form, "getlist"):
        return field_name in form
    value = form.get(field_name, default)
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "on", "si", "yes"}


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
    if suffix == "doc":
        return "DOC"
    if suffix == "png":
        return "PNG"
    if suffix in {"jpg", "jpeg"}:
        return "JPG"
    if suffix == "txt":
        return "TXT"
    if _clean(file_path).startswith(("http://", "https://")):
        return "LINK"
    return cleaned or "Altro"


def _normalize_date(value):
    cleaned = _clean(value)
    if not cleaned:
        return ""
    try:
        return date.fromisoformat(cleaned).isoformat()
    except ValueError:
        return ""


def _tags_list(value):
    return [tag.strip() for tag in (value or "").split(",") if tag.strip()]


def ensure_document_schema(conn, ensure_column):
    """Crea o aggiorna la tabella archivio documenti."""
    conn.execute(DOCUMENT_TABLE_SQL)
    for column_name, column_definition in DOCUMENT_COLUMNS.items():
        ensure_column(conn, "document_archive", column_name, column_definition)
    seed_default_documents(conn)


def seed_default_documents(conn):
    """Inserisce placeholder documentali solo se l'archivio e vuoto."""
    row = conn.execute("SELECT COUNT(*) AS total FROM document_archive").fetchone()
    if row and row["total"]:
        return
    now = _now()
    for item in DEFAULT_DOCUMENTS:
        conn.execute(
            """
            INSERT INTO document_archive
                (name, category, document_type, file_path, file_format, issuer, version,
                 tags, notes, expires_at, related_cv_id, related_job_id, is_favorite,
                 is_active, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, '', '', ?, ?, '', NULL, NULL, ?, 1, 'attivo', ?, ?)
            """,
            (
                item["name"],
                _normalize_category(item["category"]),
                item["document_type"],
                item["file_path"],
                _normalize_format(item["file_format"], item["file_path"]),
                item["tags"],
                item["notes"],
                int(item.get("is_favorite", 0)),
                now,
                now,
            ),
        )


def document_from_row(row):
    if row is None:
        return None
    document = dict(row)
    document["category"] = _normalize_category(document.get("category"))
    document["status"] = _normalize_status(document.get("status"))
    document["is_favorite"] = bool(document.get("is_favorite"))
    document["is_active"] = bool(document.get("is_active"))
    document["tags_list"] = _tags_list(document.get("tags"))
    document["created_at_label"] = (document.get("created_at") or "").replace("T", " ")
    document["updated_at_label"] = (document.get("updated_at") or "").replace("T", " ")
    document["is_expired"] = False
    expires_at = document.get("expires_at") or ""
    if expires_at:
        try:
            document["is_expired"] = date.fromisoformat(expires_at) < date.today()
        except ValueError:
            document["is_expired"] = False
    return document


def load_documents(conn, document_id=None, filters=None):
    """Carica un documento oppure l'elenco filtrato."""
    if document_id is not None:
        row = conn.execute("SELECT * FROM document_archive WHERE id = ?", (document_id,)).fetchone()
        return document_from_row(row)

    filters = filters or {}
    clauses = []
    params = []
    category = _clean(filters.get("category"))
    status = _clean(filters.get("status"))
    query = _clean(filters.get("q")).lower()

    if category in DOCUMENT_CATEGORIES:
        clauses.append("category = ?")
        params.append(category)
    if status in DOCUMENT_STATUS_OPTIONS:
        clauses.append("status = ?")
        params.append(status)
    if query:
        clauses.append(
            "(lower(name) LIKE ? OR lower(document_type) LIKE ? OR lower(tags) LIKE ? OR lower(notes) LIKE ?)"
        )
        like = f"%{query}%"
        params.extend([like, like, like, like])

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(
        f"""
        SELECT *
          FROM document_archive
          {where}
         ORDER BY is_favorite DESC, is_active DESC, updated_at DESC, id DESC
        """,
        params,
    ).fetchall()
    return [document_from_row(row) for row in rows]


def document_stats(documents):
    total = len(documents)
    favorites = sum(1 for document in documents if document.get("is_favorite"))
    expired = sum(1 for document in documents if document.get("is_expired"))
    by_category = {}
    for document in documents:
        category = document.get("category") or DEFAULT_DOCUMENT_CATEGORY
        by_category[category] = by_category.get(category, 0) + 1
    return {
        "total": total,
        "favorites": favorites,
        "expired": expired,
        "active": sum(1 for document in documents if document.get("is_active")),
        "by_category": by_category,
    }


def save_document(conn, form, document_id=None):
    now = _now()
    name = _clean(form.get("name")) or "Documento senza nome"
    file_path = _clean(form.get("file_path"))
    values = {
        "name": name,
        "category": _normalize_category(form.get("category")),
        "document_type": _clean(form.get("document_type")),
        "file_path": file_path,
        "file_format": _normalize_format(form.get("file_format"), file_path),
        "issuer": _clean(form.get("issuer")),
        "version": _clean(form.get("version")),
        "tags": _clean(form.get("tags")),
        "notes": _clean(form.get("notes")),
        "expires_at": _normalize_date(form.get("expires_at")),
        "is_favorite": 1 if _checked(form, "is_favorite") else 0,
        "is_active": 1 if _checked(form, "is_active", True) else 0,
        "status": _normalize_status(form.get("status")),
        "updated_at": now,
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
    document = load_documents(conn, document_id)
    if document is None:
        return False
    conn.execute("DELETE FROM document_archive WHERE id = ?", (document_id,))
    return True


def toggle_favorite_document(conn, document_id):
    document = load_documents(conn, document_id)
    if document is None:
        return False
    conn.execute(
        "UPDATE document_archive SET is_favorite = ?, updated_at = ? WHERE id = ?",
        (0 if document["is_favorite"] else 1, _now(), document_id),
    )
    return True
