"""Concorsi pubblici per Radar Lavoro.

Il modulo gestisce bandi, scadenze, stato della domanda e collegamenti ai
documenti locali. I file restano nell'Archivio Documenti: qui vengono salvati
solo metadati e riferimenti.
"""

import json
from datetime import date, datetime


COMPETITION_CATEGORIES = [
    "Comunicazione",
    "Ufficio stampa",
    "Amministrativo",
    "Categorie protette",
    "Digital",
    "Data Analyst",
    "Web",
    "Altro",
]

COMPETITION_STATUS_OPTIONS = {
    "monitorato": "Monitorato",
    "aperto": "Aperto",
    "in_scadenza": "In scadenza",
    "chiuso": "Chiuso",
    "prove": "Prove",
    "graduatoria": "Graduatoria",
    "archiviato": "Archiviato",
}

COMPETITION_APPLICATION_STATUS_OPTIONS = {
    "da_valutare": "Da valutare",
    "in_preparazione": "In preparazione",
    "inviata": "Domanda inviata",
    "prove": "Prove da seguire",
    "idoneo": "Idoneita/graduatoria",
    "non_idoneo": "Non idoneo",
    "rinunciato": "Rinunciato",
}

COMPETITION_ARCHIVE_FILTER_OPTIONS = {
    "attivi": "Solo attivi",
    "tutti": "Tutti",
    "archiviati": "Solo archiviati",
}

DEFAULT_COMPETITION_CATEGORY = "Altro"
DEFAULT_COMPETITION_STATUS = "monitorato"
DEFAULT_APPLICATION_STATUS = "da_valutare"

PUBLIC_COMPETITIONS_TABLE_SQL = """
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
)
"""

PUBLIC_COMPETITION_COLUMNS = {
    "title": "TEXT DEFAULT ''",
    "organization": "TEXT DEFAULT ''",
    "category": "TEXT DEFAULT 'Altro'",
    "location": "TEXT DEFAULT ''",
    "source_url": "TEXT DEFAULT ''",
    "positions_count": "INTEGER DEFAULT 0",
    "contract_type": "TEXT DEFAULT ''",
    "competition_status": "TEXT DEFAULT 'monitorato'",
    "application_status": "TEXT DEFAULT 'da_valutare'",
    "published_at": "TEXT DEFAULT ''",
    "application_opens_at": "TEXT DEFAULT ''",
    "deadline_at": "TEXT DEFAULT ''",
    "written_exam_at": "TEXT DEFAULT ''",
    "oral_exam_at": "TEXT DEFAULT ''",
    "ranking_at": "TEXT DEFAULT ''",
    "requirements": "TEXT DEFAULT ''",
    "required_documents": "TEXT DEFAULT '[]'",
    "personal_notes": "TEXT DEFAULT ''",
    "is_archived": "INTEGER DEFAULT 0",
    "created_at": "TEXT DEFAULT ''",
    "updated_at": "TEXT DEFAULT ''",
}

COMPETITION_DOCUMENTS_TABLE_SQL = """
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
)
"""

COMPETITION_DOCUMENT_COLUMNS = {
    "competition_id": "INTEGER DEFAULT 0",
    "document_id": "INTEGER DEFAULT 0",
    "purpose": "TEXT DEFAULT ''",
    "is_required": "INTEGER DEFAULT 1",
    "is_ready": "INTEGER DEFAULT 0",
    "notes": "TEXT DEFAULT ''",
    "created_at": "TEXT DEFAULT ''",
    "updated_at": "TEXT DEFAULT ''",
}


def _now():
    return datetime.now().isoformat(timespec="minutes")


def _today():
    return date.today()


def _clean(value):
    return (value or "").strip()


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


def _split_lines(value):
    return [line.strip() for line in (value or "").splitlines() if line.strip()]


def _load_json_list(value):
    try:
        parsed = json.loads(value or "[]")
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def _dump_json_list(values):
    return json.dumps(values or [], ensure_ascii=False)


def _normalize_category(category):
    cleaned = _clean(category)
    return cleaned if cleaned in COMPETITION_CATEGORIES else DEFAULT_COMPETITION_CATEGORY


def _normalize_competition_status(status):
    cleaned = _clean(status)
    return cleaned if cleaned in COMPETITION_STATUS_OPTIONS else DEFAULT_COMPETITION_STATUS


def _normalize_application_status(status):
    cleaned = _clean(status)
    return cleaned if cleaned in COMPETITION_APPLICATION_STATUS_OPTIONS else DEFAULT_APPLICATION_STATUS


def _normalize_archive_filter(value):
    cleaned = _clean(value)
    return cleaned if cleaned in COMPETITION_ARCHIVE_FILTER_OPTIONS else "attivi"


def _normalize_date(value):
    cleaned = _clean(value)
    if not cleaned:
        return ""
    try:
        return date.fromisoformat(cleaned).isoformat()
    except ValueError:
        return ""


def _parse_date(value):
    try:
        return date.fromisoformat(value or "")
    except ValueError:
        return None


def ensure_public_competitions_schema(conn, ensure_column):
    """Crea e aggiorna le tabelle concorsi senza perdere dati esistenti."""
    conn.execute(PUBLIC_COMPETITIONS_TABLE_SQL)
    for column_name, column_definition in PUBLIC_COMPETITION_COLUMNS.items():
        ensure_column(conn, "public_competitions", column_name, column_definition)

    conn.execute(COMPETITION_DOCUMENTS_TABLE_SQL)
    for column_name, column_definition in COMPETITION_DOCUMENT_COLUMNS.items():
        ensure_column(conn, "competition_documents", column_name, column_definition)


def competition_filters_from_args(args):
    competition_status = _clean(args.get("competition_status"))
    application_status = _clean(args.get("application_status"))
    return {
        "q": _clean(args.get("q")),
        "competition_status": competition_status if competition_status in COMPETITION_STATUS_OPTIONS else "",
        "application_status": (
            application_status
            if application_status in COMPETITION_APPLICATION_STATUS_OPTIONS
            else ""
        ),
        "archive_filter": _normalize_archive_filter(args.get("archive_filter")),
    }


def calculate_application_completeness(required_documents, linked_documents):
    required_items = required_documents or []
    required_links = [document for document in linked_documents if document.get("is_required")]
    total_required = max(len(required_items), len(required_links))
    ready_required = sum(1 for document in required_links if document.get("is_ready"))

    if total_required <= 0:
        return {
            "completion_percentage": 0,
            "completion_label": "Documenti da definire",
            "required_total": 0,
            "required_ready": 0,
            "required_missing": 0,
        }

    percentage = round((ready_required / total_required) * 100)
    missing = max(total_required - ready_required, 0)
    label = "Completa" if percentage == 100 else f"{ready_required}/{total_required} documenti pronti"
    return {
        "completion_percentage": percentage,
        "completion_label": label,
        "required_total": total_required,
        "required_ready": ready_required,
        "required_missing": missing,
    }


def competition_document_from_row(row):
    if row is None:
        return None
    link = dict(row)
    link["is_required"] = bool(link.get("is_required"))
    link["is_ready"] = bool(link.get("is_ready"))
    link["created_at_label"] = (link.get("created_at") or "").replace("T", " ")
    link["updated_at_label"] = (link.get("updated_at") or "").replace("T", " ")
    return link


def load_competition_documents(conn, competition_id):
    rows = conn.execute(
        """
        SELECT cd.*,
               da.title AS document_title,
               da.category AS document_category,
               da.file_path AS document_file_path,
               da.file_format AS document_file_format,
               da.status AS document_status
          FROM competition_documents cd
          LEFT JOIN document_archive da ON da.id = cd.document_id
         WHERE cd.competition_id = ?
         ORDER BY cd.is_required DESC, cd.is_ready DESC, cd.updated_at DESC, cd.id DESC
        """,
        (competition_id,),
    ).fetchall()
    return [competition_document_from_row(row) for row in rows]


def _enrich_competition(conn, competition):
    linked_documents = load_competition_documents(conn, competition["id"])
    competition["linked_documents"] = linked_documents
    competition.update(
        calculate_application_completeness(competition["required_documents"], linked_documents)
    )
    return competition


def competition_from_row(row):
    if row is None:
        return None
    competition = dict(row)
    competition["category"] = _normalize_category(competition.get("category"))
    competition["competition_status"] = _normalize_competition_status(competition.get("competition_status"))
    competition["application_status"] = _normalize_application_status(competition.get("application_status"))
    competition["competition_status_label"] = COMPETITION_STATUS_OPTIONS[competition["competition_status"]]
    competition["application_status_label"] = COMPETITION_APPLICATION_STATUS_OPTIONS[competition["application_status"]]
    competition["required_documents"] = _load_json_list(competition.get("required_documents"))
    competition["is_archived"] = bool(competition.get("is_archived"))
    competition["created_at_label"] = (competition.get("created_at") or "").replace("T", " ")
    competition["updated_at_label"] = (competition.get("updated_at") or "").replace("T", " ")

    deadline = _parse_date(competition.get("deadline_at"))
    competition["days_to_deadline"] = None
    competition["is_deadline_soon"] = False
    competition["is_deadline_expired"] = False
    if deadline:
        days = (deadline - _today()).days
        competition["days_to_deadline"] = days
        competition["is_deadline_soon"] = 0 <= days <= 7 and not competition["is_archived"]
        competition["is_deadline_expired"] = days < 0 and not competition["is_archived"]
    return competition


def load_competitions(conn, competition_id=None, filters=None):
    """Carica un concorso specifico oppure l'elenco filtrato."""
    if competition_id is not None:
        row = conn.execute("SELECT * FROM public_competitions WHERE id = ?", (competition_id,)).fetchone()
        competition = competition_from_row(row)
        return _enrich_competition(conn, competition) if competition else None

    filters = filters or {}
    clauses = []
    params = []
    query = _clean(filters.get("q")).lower()
    competition_status = _clean(filters.get("competition_status"))
    application_status = _clean(filters.get("application_status"))
    archive_filter = _normalize_archive_filter(filters.get("archive_filter"))

    if query:
        clauses.append(
            """(
                LOWER(title) LIKE ?
                OR LOWER(organization) LIKE ?
                OR LOWER(category) LIKE ?
                OR LOWER(location) LIKE ?
                OR LOWER(requirements) LIKE ?
                OR LOWER(personal_notes) LIKE ?
            )"""
        )
        like_query = f"%{query}%"
        params.extend([like_query] * 6)

    if competition_status in COMPETITION_STATUS_OPTIONS:
        clauses.append("competition_status = ?")
        params.append(competition_status)

    if application_status in COMPETITION_APPLICATION_STATUS_OPTIONS:
        clauses.append("application_status = ?")
        params.append(application_status)

    if archive_filter == "archiviati":
        clauses.append("is_archived = 1")
    elif archive_filter == "attivi":
        clauses.append("is_archived = 0")

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(
        f"""
        SELECT *
          FROM public_competitions
          {where}
         ORDER BY is_archived ASC,
                  CASE WHEN deadline_at = '' THEN 1 ELSE 0 END,
                  deadline_at ASC,
                  updated_at DESC,
                  id DESC
        """,
        tuple(params),
    ).fetchall()
    return [_enrich_competition(conn, competition_from_row(row)) for row in rows]


def save_competition(conn, form, competition_id=None):
    """Inserisce o aggiorna un concorso pubblico."""
    now = _now()
    existing = load_competitions(conn, competition_id) if competition_id else None
    if competition_id and existing is None:
        competition_id = None

    competition_status = _normalize_competition_status(form.get("competition_status"))
    is_archived = 1 if _checked(form, "is_archived", False) or competition_status == "archiviato" else 0
    if is_archived:
        competition_status = "archiviato"

    values = {
        "title": _clean(form.get("title")) or "Concorso senza titolo",
        "organization": _clean(form.get("organization")),
        "category": _normalize_category(form.get("category")),
        "location": _clean(form.get("location")),
        "source_url": _clean(form.get("source_url")),
        "positions_count": _int_from_form(form, "positions_count"),
        "contract_type": _clean(form.get("contract_type")),
        "competition_status": competition_status,
        "application_status": _normalize_application_status(form.get("application_status")),
        "published_at": _normalize_date(form.get("published_at")),
        "application_opens_at": _normalize_date(form.get("application_opens_at")),
        "deadline_at": _normalize_date(form.get("deadline_at")),
        "written_exam_at": _normalize_date(form.get("written_exam_at")),
        "oral_exam_at": _normalize_date(form.get("oral_exam_at")),
        "ranking_at": _normalize_date(form.get("ranking_at")),
        "requirements": _clean(form.get("requirements")),
        "required_documents": _dump_json_list(_split_lines(form.get("required_documents", ""))),
        "personal_notes": _clean(form.get("personal_notes")),
        "is_archived": is_archived,
        "updated_at": now,
    }

    if competition_id:
        assignments = ", ".join(f"{column} = ?" for column in values)
        conn.execute(
            f"UPDATE public_competitions SET {assignments} WHERE id = ?",
            tuple(values.values()) + (competition_id,),
        )
    else:
        values["created_at"] = now
        columns = ", ".join(values.keys())
        placeholders = ", ".join("?" for _ in values)
        cursor = conn.execute(
            f"INSERT INTO public_competitions ({columns}) VALUES ({placeholders})",
            tuple(values.values()),
        )
        competition_id = cursor.lastrowid
    return competition_id


def delete_competition(conn, competition_id):
    competition = load_competitions(conn, competition_id)
    if competition is None:
        return False
    conn.execute("DELETE FROM competition_documents WHERE competition_id = ?", (competition_id,))
    conn.execute("DELETE FROM public_competitions WHERE id = ?", (competition_id,))
    return True


def archive_competition(conn, competition_id):
    competition = load_competitions(conn, competition_id)
    if competition is None:
        return False
    conn.execute(
        """
        UPDATE public_competitions
           SET is_archived = 1,
               competition_status = 'archiviato',
               updated_at = ?
         WHERE id = ?
        """,
        (_now(), competition_id),
    )
    return True


def link_competition_document(conn, competition_id, form):
    competition = load_competitions(conn, competition_id)
    if competition is None:
        return False

    document_id = _int_from_form(form, "document_id")
    if document_id <= 0:
        return False

    now = _now()
    values = {
        "competition_id": competition_id,
        "document_id": document_id,
        "purpose": _clean(form.get("purpose")) or "Documento domanda",
        "is_required": 1 if _checked(form, "is_required", True) else 0,
        "is_ready": 1 if _checked(form, "is_ready", False) else 0,
        "notes": _clean(form.get("notes")),
        "updated_at": now,
    }
    existing = conn.execute(
        """
        SELECT id
          FROM competition_documents
         WHERE competition_id = ? AND document_id = ?
        """,
        (competition_id, document_id),
    ).fetchone()
    if existing:
        assignments = ", ".join(f"{column} = ?" for column in values)
        conn.execute(
            f"UPDATE competition_documents SET {assignments} WHERE id = ?",
            tuple(values.values()) + (existing["id"],),
        )
    else:
        values["created_at"] = now
        columns = ", ".join(values.keys())
        placeholders = ", ".join("?" for _ in values)
        conn.execute(
            f"INSERT INTO competition_documents ({columns}) VALUES ({placeholders})",
            tuple(values.values()),
        )
    return True


def remove_competition_document(conn, competition_id, link_id):
    row = conn.execute(
        """
        SELECT id
          FROM competition_documents
         WHERE id = ? AND competition_id = ?
        """,
        (link_id, competition_id),
    ).fetchone()
    if row is None:
        return False
    conn.execute("DELETE FROM competition_documents WHERE id = ?", (link_id,))
    return True


def competition_stats(competitions):
    stats = {
        "totali": 0,
        "in_preparazione": 0,
        "domande_inviate": 0,
        "scadenze_7": 0,
        "idoneita_graduatorie": 0,
        "archiviati": 0,
    }
    for competition in competitions:
        if competition.get("is_archived"):
            stats["archiviati"] += 1
        else:
            stats["totali"] += 1
        if competition.get("application_status") == "in_preparazione":
            stats["in_preparazione"] += 1
        if competition.get("application_status") in {"inviata", "prove", "idoneo"}:
            stats["domande_inviate"] += 1
        if competition.get("is_deadline_soon"):
            stats["scadenze_7"] += 1
        if (
            competition.get("application_status") == "idoneo"
            or competition.get("competition_status") == "graduatoria"
        ):
            stats["idoneita_graduatorie"] += 1
    return stats


def dashboard_competition_stats(conn):
    competitions = load_competitions(conn, filters={"archive_filter": "attivi"})
    return competition_stats(competitions)
