"""CV Manager per Radar Lavoro.

Il modulo gestisce solo metadati e percorsi locali dei curriculum. I file CV
restano sul computer dell'utente e non vengono salvati nel database.
"""

from datetime import datetime
from pathlib import Path


CV_CATEGORIES = [
    "Corporate Communication",
    "Digital Marketing",
    "Giornalismo",
    "Comunicazione istituzionale",
    "Data Analyst",
    "Web Developer",
    "Generico",
]

CV_FORMAT_OPTIONS = ["PDF", "DOCX", "TXT", "LINK", "Altro"]
DEFAULT_CV_CATEGORY = "Generico"

CV_TABLE_SQL = """
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
)
"""

CV_COLUMNS = {
    "name": "TEXT DEFAULT ''",
    "description": "TEXT DEFAULT ''",
    "version": "TEXT DEFAULT ''",
    "category": "TEXT DEFAULT 'Generico'",
    "file_path": "TEXT DEFAULT ''",
    "file_format": "TEXT DEFAULT ''",
    "checksum": "TEXT DEFAULT ''",
    "created_at": "TEXT DEFAULT ''",
    "updated_at": "TEXT DEFAULT ''",
    "is_active": "INTEGER DEFAULT 1",
    "is_default": "INTEGER DEFAULT 0",
    "notes": "TEXT DEFAULT ''",
}

CATEGORY_RULES = {
    "Digital Marketing": [
        "marketing",
        "digital marketing",
        "social media",
        "seo",
        "sem",
        "adv",
        "campagne",
        "content marketing",
    ],
    "Web Developer": [
        "developer",
        "sviluppatore",
        "web developer",
        "full stack",
        "frontend",
        "backend",
        "html",
        "css",
        "javascript",
        "python",
        "php",
        "laravel",
    ],
    "Giornalismo": [
        "giornalista",
        "giornalismo",
        "redattore",
        "redazione",
        "editor",
        "stampa",
    ],
    "Comunicazione istituzionale": [
        "comunicazione istituzionale",
        "comunicazione pubblica",
        "pubblica amministrazione",
        "ente pubblico",
        "ufficio stampa",
        "pa",
    ],
    "Data Analyst": [
        "data analyst",
        "analyst",
        "analisi dati",
        "analytics",
        "sql",
        "dashboard",
        "report",
        "excel",
        "power bi",
    ],
    "Corporate Communication": [
        "corporate communication",
        "comunicazione corporate",
        "comunicazione aziendale",
        "media relation",
        "public relation",
        "pr",
        "comunicazione interna",
    ],
}


def _now():
    return datetime.now().isoformat(timespec="minutes")


def _clean(value):
    return (value or "").strip()


def _normalize_text(value):
    return " ".join((value or "").lower().split())


def _normalize_category(category):
    cleaned = _clean(category)
    return cleaned if cleaned in CV_CATEGORIES else DEFAULT_CV_CATEGORY


def _normalize_format(file_format, file_path):
    cleaned = _clean(file_format)
    if cleaned in CV_FORMAT_OPTIONS:
        return cleaned
    suffix = Path(_clean(file_path)).suffix.lower().replace(".", "")
    if suffix == "pdf":
        return "PDF"
    if suffix == "docx":
        return "DOCX"
    if suffix == "txt":
        return "TXT"
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


def ensure_cv_schema(conn, ensure_column):
    """Crea e aggiorna la tabella dei CV mantenendo compatibilita retroattiva."""
    conn.execute(CV_TABLE_SQL)
    for column_name, column_definition in CV_COLUMNS.items():
        ensure_column(conn, "cv_documents", column_name, column_definition)


def cv_from_row(row):
    if row is None:
        return None
    cv = dict(row)
    cv["category"] = _normalize_category(cv.get("category"))
    cv["is_active"] = bool(cv.get("is_active"))
    cv["is_default"] = bool(cv.get("is_default"))
    cv["created_at_label"] = (cv.get("created_at") or "").replace("T", " ")
    cv["updated_at_label"] = (cv.get("updated_at") or "").replace("T", " ")
    return cv


def load_cv(conn, cv_id=None):
    """Carica un CV specifico oppure tutti i CV ordinati per priorita."""
    if cv_id is not None:
        row = conn.execute("SELECT * FROM cv_documents WHERE id = ?", (cv_id,)).fetchone()
        return cv_from_row(row)
    rows = conn.execute(
        """
        SELECT *
          FROM cv_documents
         ORDER BY is_default DESC, is_active DESC, category ASC, updated_at DESC, id DESC
        """
    ).fetchall()
    return [cv_from_row(row) for row in rows]


def save_cv(conn, form, cv_id=None):
    """Inserisce o aggiorna un CV salvando solo metadati e percorso locale."""
    now = _now()
    name = _clean(form.get("name")) or "CV senza nome"
    file_path = _clean(form.get("file_path"))
    file_format = _normalize_format(form.get("file_format"), file_path)
    category = _normalize_category(form.get("category"))
    is_active = 1 if _checked(form, "is_active", True) else 0
    should_be_default = _checked(form, "is_default", False)
    values = {
        "name": name,
        "description": _clean(form.get("description")),
        "version": _clean(form.get("version")),
        "category": category,
        "file_path": file_path,
        "file_format": file_format,
        "checksum": _clean(form.get("checksum")),
        "updated_at": now,
        "is_active": is_active,
        "notes": _clean(form.get("notes")),
    }

    if cv_id:
        existing = load_cv(conn, cv_id)
        if existing is None:
            cv_id = None

    if cv_id:
        assignments = ", ".join(f"{column} = ?" for column in values)
        conn.execute(
            f"UPDATE cv_documents SET {assignments} WHERE id = ?",
            tuple(values.values()) + (cv_id,),
        )
    else:
        values["created_at"] = now
        columns = ", ".join(values.keys())
        placeholders = ", ".join("?" for _ in values)
        cursor = conn.execute(
            f"INSERT INTO cv_documents ({columns}) VALUES ({placeholders})",
            tuple(values.values()),
        )
        cv_id = cursor.lastrowid

    if should_be_default:
        set_default_cv(conn, cv_id)

    return cv_id


def delete_cv(conn, cv_id):
    """Elimina solo il record del CV, mai il file indicato dal percorso."""
    cv = load_cv(conn, cv_id)
    if cv is None:
        return False
    conn.execute("DELETE FROM cv_documents WHERE id = ?", (cv_id,))
    if cv["is_default"]:
        fallback = conn.execute(
            """
            SELECT id
              FROM cv_documents
             WHERE is_active = 1
             ORDER BY updated_at DESC, id DESC
             LIMIT 1
            """
        ).fetchone()
        if fallback:
            set_default_cv(conn, fallback["id"])
    return True


def set_default_cv(conn, cv_id):
    cv = load_cv(conn, cv_id)
    if cv is None:
        return False
    now = _now()
    conn.execute("UPDATE cv_documents SET is_default = 0")
    conn.execute(
        """
        UPDATE cv_documents
           SET is_default = 1, is_active = 1, updated_at = ?
         WHERE id = ?
        """,
        (now, cv_id),
    )
    return True


def _job_text(job_or_text):
    if isinstance(job_or_text, dict):
        parts = [
            job_or_text.get("title"),
            job_or_text.get("company"),
            job_or_text.get("location"),
            job_or_text.get("snippet"),
            job_or_text.get("matched_query"),
        ]
        return _normalize_text(" ".join(part or "" for part in parts))
    return _normalize_text(job_or_text)


def _best_category_for_text(text):
    best_category = DEFAULT_CV_CATEGORY
    best_score = 0
    for category, keywords in CATEGORY_RULES.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > best_score:
            best_category = category
            best_score = score
    return best_category, best_score


def find_best_cv(conn, job_or_text=None):
    """Suggerisce un CV attivo con regole semplici, pronte per Radar AI."""
    text = _job_text(job_or_text or "")
    category, score = _best_category_for_text(text)
    if score:
        row = conn.execute(
            """
            SELECT *
              FROM cv_documents
             WHERE is_active = 1 AND category = ?
             ORDER BY is_default DESC, updated_at DESC, id DESC
             LIMIT 1
            """,
            (category,),
        ).fetchone()
        if row:
            cv = cv_from_row(row)
            cv["suggestion_reason"] = f"Regole semplici: testo coerente con {category}."
            return cv

    row = conn.execute(
        """
        SELECT *
          FROM cv_documents
         WHERE is_active = 1 AND is_default = 1
         ORDER BY updated_at DESC, id DESC
         LIMIT 1
        """
    ).fetchone()
    if row:
        cv = cv_from_row(row)
        cv["suggestion_reason"] = "CV predefinito in attesa del suggerimento Radar AI."
        return cv

    row = conn.execute(
        """
        SELECT *
          FROM cv_documents
         WHERE is_active = 1
         ORDER BY updated_at DESC, id DESC
         LIMIT 1
        """
    ).fetchone()
    if row:
        cv = cv_from_row(row)
        cv["suggestion_reason"] = "Primo CV attivo disponibile."
        return cv
    return None
