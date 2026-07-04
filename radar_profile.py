"""Profilo professionale personale per Radar Lavoro.

Il modulo conserva una scheda strutturata del profilo di Andrea. I dati sono
salvati nella tabella `profile`, per restare compatibili con l'app monoutente
e con i prossimi sprint: CV Manager, documenti, concorsi, Radar AI e ranking.
"""

import json
from datetime import datetime


LEGACY_DEFAULT_HEADLINE = "Corporate Communication, Digital Marketing e contenuti digitali"
LEGACY_DEFAULT_EDUCATION = "Laurea Magistrale in Corporate Communication - Universita degli Studi di Salerno"
PROFILE_SCHEMA_VERSION = "profilo_strutturato_v1"

DEFAULT_PROFILE = {
    "full_name": "Andrea Bartiromo",
    "headline": (
        "Studente Magistrale in Corporate Communication | Comunicazione Digitale | "
        "Digital Marketing | Content Creation | Giornalismo | Full Stack Web Development"
    ),
    "education_items": [
        "Laurea Magistrale in Corporate Communication, Universita degli Studi di Salerno, in corso",
        "Laurea Triennale in Scienze della Comunicazione, Universita degli Studi di Salerno",
        "Hackademy+ Full Stack Web Developer, Aulab",
    ],
    "experiences": [
        "Apprendista Giornalista, Nuovo Nocera, 2024 - oggi",
        "Social Media Manager, Universita degli Studi di Salerno, 2021 - 2022",
    ],
    "certifications": [
        "Cisco Cybersecurity",
        "Python Programming",
        "Data Analyst",
        "AI Avanzata",
        "EIPASS 7 Moduli",
    ],
    "skills": [
        "Corporate Communication",
        "Comunicazione Digitale",
        "Content Marketing",
        "Social Media Management",
        "Digital Marketing",
        "SEO",
        "SEM",
        "Copywriting",
        "Content Creation",
        "Web Analytics",
        "Giornalismo",
        "Ufficio Stampa",
    ],
    "technical_skills": [
        "HTML",
        "CSS",
        "JavaScript",
        "PHP",
        "Laravel",
        "Python",
        "MySQL",
        "API REST",
        "Git",
        "GitHub",
        "VS Code",
        "Postman",
        "Canva",
        "Figma",
        "Microsoft Office",
    ],
    "target_roles": [
        "Addetto Comunicazione",
        "Corporate Communication Specialist Junior",
        "Digital Marketing Assistant",
        "Social Media Specialist",
        "Content Creator",
        "Copywriter",
        "Web Content Editor",
        "Ufficio Stampa",
        "Redattore",
        "Digital Communication Specialist",
        "Junior Data Analyst",
        "Web Developer Junior",
        "Operatore Amministrativo Categorie Protette",
        "Communication Officer",
        "Marketing Assistant",
    ],
    "territorial_preferences": [
        "Provincia di Salerno",
        "Campania",
        "Remoto",
        "Ibrido",
        "Disponibile a valutare tutta Italia per opportunita di particolare interesse",
    ],
    "protected_categories": [
        "Art.1 Legge 68/99",
        "Invalidita civile 75%",
    ],
    "availability": (
        "Disponibile per opportunita junior, comunicazione digitale, marketing, "
        "giornalismo, sviluppo web, remoto/ibrido e categorie protette."
    ),
    "notes": (
        "Profilo strutturato per guidare ranking, CV Manager, archivio documenti, "
        "concorsi pubblici, Radar AI e motore di apprendimento."
    ),
}

PROFILE_COLUMNS = {
    "professional_full_name": "TEXT DEFAULT ''",
    "professional_headline": "TEXT DEFAULT ''",
    "education": "TEXT DEFAULT ''",
    "education_items": "TEXT DEFAULT '[]'",
    "experiences": "TEXT DEFAULT '[]'",
    "certifications": "TEXT DEFAULT '[]'",
    "location_preference": "TEXT DEFAULT ''",
    "territorial_preferences": "TEXT DEFAULT '[]'",
    "availability": "TEXT DEFAULT ''",
    "protected_category_notes": "TEXT DEFAULT ''",
    "protected_categories": "TEXT DEFAULT '[]'",
    "strong_preferences": "TEXT DEFAULT '[]'",
    "soft_preferences": "TEXT DEFAULT '[]'",
    "skills": "TEXT DEFAULT '[]'",
    "technical_skills": "TEXT DEFAULT '[]'",
    "target_roles": "TEXT DEFAULT '[]'",
    "profile_notes": "TEXT DEFAULT ''",
    "profile_updated_at": "TEXT DEFAULT ''",
    "profile_schema_version": "TEXT DEFAULT ''",
}

LIST_FIELDS = [
    "education_items",
    "experiences",
    "certifications",
    "skills",
    "technical_skills",
    "target_roles",
    "territorial_preferences",
    "protected_categories",
    "strong_preferences",
    "soft_preferences",
]


def _load_json_list(value):
    try:
        parsed = json.loads(value or "[]")
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def _dump_json_list(values):
    return json.dumps(values or [], ensure_ascii=False)


def _row_value(row, key, default=""):
    return row[key] if key in row.keys() else default


def _merge_lists(existing, defaults):
    merged = []
    for value in (existing or []) + (defaults or []):
        cleaned = (value or "").strip()
        if cleaned and cleaned not in merged:
            merged.append(cleaned)
    return merged


def split_lines(value):
    return [line.strip() for line in (value or "").splitlines() if line.strip()]


def join_lines(values):
    return "\n".join(values or [])


def list_from_form(form, field_name):
    return split_lines(form.get(field_name, ""))


def ensure_professional_profile_columns(conn, ensure_column):
    """Aggiunge le colonne del profilo alla tabella profile senza perdere dati."""
    for column_name, column_definition in PROFILE_COLUMNS.items():
        ensure_column(conn, "profile", column_name, column_definition)


def _default_strong_preferences():
    return [
        "Categorie protette L.68/99",
        "Art.1 Legge 68/99",
        "Invalidita civile 75%",
        "Provincia di Salerno",
        "Campania",
        "Remoto",
        "Ibrido",
        "Comunicazione Digitale",
        "Corporate Communication",
    ]


def _default_soft_preferences():
    return [
        "Digital Marketing",
        "Content Creation",
        "Giornalismo",
        "Ufficio Stampa",
        "Junior Data Analyst",
        "Web Developer Junior",
        "Tutta Italia per opportunita di particolare interesse",
    ]


def seed_professional_profile(conn):
    """Compila o arricchisce il profilo iniziale senza cancellare dati esistenti."""
    row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    if row is None:
        return

    updates = {}
    headline = _row_value(row, "professional_headline")
    education = _row_value(row, "education")
    should_enrich_defaults = _row_value(row, "profile_schema_version") != PROFILE_SCHEMA_VERSION

    if not _row_value(row, "professional_full_name"):
        updates["professional_full_name"] = DEFAULT_PROFILE["full_name"]
    if not headline or (should_enrich_defaults and headline == LEGACY_DEFAULT_HEADLINE):
        updates["professional_headline"] = DEFAULT_PROFILE["headline"]
    if not education or (should_enrich_defaults and education == LEGACY_DEFAULT_EDUCATION):
        updates["education"] = join_lines(DEFAULT_PROFILE["education_items"])
    if not _row_value(row, "availability"):
        updates["availability"] = DEFAULT_PROFILE["availability"]
    if not _row_value(row, "location_preference"):
        updates["location_preference"] = join_lines(DEFAULT_PROFILE["territorial_preferences"])
    if not _row_value(row, "protected_category_notes"):
        updates["protected_category_notes"] = join_lines(DEFAULT_PROFILE["protected_categories"])
    if not _row_value(row, "profile_notes"):
        updates["profile_notes"] = DEFAULT_PROFILE["notes"]

    defaults_by_field = {
        "education_items": DEFAULT_PROFILE["education_items"],
        "experiences": DEFAULT_PROFILE["experiences"],
        "certifications": DEFAULT_PROFILE["certifications"],
        "skills": DEFAULT_PROFILE["skills"],
        "technical_skills": DEFAULT_PROFILE["technical_skills"],
        "target_roles": DEFAULT_PROFILE["target_roles"],
        "territorial_preferences": DEFAULT_PROFILE["territorial_preferences"],
        "protected_categories": DEFAULT_PROFILE["protected_categories"],
        "strong_preferences": _default_strong_preferences(),
        "soft_preferences": _default_soft_preferences(),
    }
    for field_name, default_values in defaults_by_field.items():
        existing = _load_json_list(_row_value(row, field_name, "[]"))
        merged = _merge_lists(existing, default_values) if should_enrich_defaults else existing
        if merged != existing:
            updates[field_name] = _dump_json_list(merged)

    if should_enrich_defaults:
        updates["profile_schema_version"] = PROFILE_SCHEMA_VERSION
    if not updates:
        return

    updates["profile_updated_at"] = datetime.now().isoformat(timespec="minutes")
    assignments = ", ".join(f"{column} = ?" for column in updates)
    conn.execute(
        f"UPDATE profile SET {assignments} WHERE id = 1",
        tuple(updates.values()),
    )


def profile_from_row(row):
    education_items = (
        _load_json_list(_row_value(row, "education_items", "[]"))
        or split_lines(_row_value(row, "education"))
        or DEFAULT_PROFILE["education_items"]
    )
    territorial_preferences = (
        _load_json_list(_row_value(row, "territorial_preferences", "[]"))
        or split_lines(_row_value(row, "location_preference"))
        or DEFAULT_PROFILE["territorial_preferences"]
    )
    protected_categories = (
        _load_json_list(_row_value(row, "protected_categories", "[]"))
        or split_lines(_row_value(row, "protected_category_notes"))
        or DEFAULT_PROFILE["protected_categories"]
    )
    profile = {
        "professional_full_name": _row_value(row, "professional_full_name") or DEFAULT_PROFILE["full_name"],
        "professional_headline": _row_value(row, "professional_headline") or DEFAULT_PROFILE["headline"],
        "education_items": education_items,
        "experiences": _load_json_list(_row_value(row, "experiences", "[]")) or DEFAULT_PROFILE["experiences"],
        "certifications": _load_json_list(_row_value(row, "certifications", "[]")) or DEFAULT_PROFILE["certifications"],
        "skills": _load_json_list(_row_value(row, "skills", "[]")) or DEFAULT_PROFILE["skills"],
        "technical_skills": _load_json_list(_row_value(row, "technical_skills", "[]")) or DEFAULT_PROFILE["technical_skills"],
        "target_roles": _load_json_list(_row_value(row, "target_roles", "[]")) or DEFAULT_PROFILE["target_roles"],
        "territorial_preferences": territorial_preferences,
        "protected_categories": protected_categories,
        "availability": _row_value(row, "availability") or DEFAULT_PROFILE["availability"],
        "strong_preferences": _load_json_list(_row_value(row, "strong_preferences", "[]")) or _default_strong_preferences(),
        "soft_preferences": _load_json_list(_row_value(row, "soft_preferences", "[]")) or _default_soft_preferences(),
        "profile_notes": _row_value(row, "profile_notes"),
        "profile_updated_at": _row_value(row, "profile_updated_at"),
        "profile_schema_version": _row_value(row, "profile_schema_version"),
    }
    profile["education"] = join_lines(profile["education_items"])
    profile["location_preference"] = join_lines(profile["territorial_preferences"])
    profile["protected_category_notes"] = join_lines(profile["protected_categories"])
    return profile


def load_professional_profile(conn):
    row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    if row is None:
        profile = DEFAULT_PROFILE.copy()
        profile["professional_full_name"] = DEFAULT_PROFILE["full_name"]
        profile["professional_headline"] = DEFAULT_PROFILE["headline"]
        profile["profile_notes"] = DEFAULT_PROFILE["notes"]
        profile["profile_updated_at"] = ""
        profile["education"] = join_lines(DEFAULT_PROFILE["education_items"])
        profile["location_preference"] = join_lines(DEFAULT_PROFILE["territorial_preferences"])
        profile["protected_category_notes"] = join_lines(DEFAULT_PROFILE["protected_categories"])
        profile["strong_preferences"] = _default_strong_preferences()
        profile["soft_preferences"] = _default_soft_preferences()
        profile["profile_schema_version"] = PROFILE_SCHEMA_VERSION
        return profile
    return profile_from_row(row)


def save_professional_profile(conn, form):
    education_items = list_from_form(form, "education_items")
    territorial_preferences = list_from_form(form, "territorial_preferences")
    protected_categories = list_from_form(form, "protected_categories")
    skills = list_from_form(form, "skills")
    technical_skills = list_from_form(form, "technical_skills")
    target_roles = list_from_form(form, "target_roles")
    experiences = list_from_form(form, "experiences")
    certifications = list_from_form(form, "certifications")
    strong_preferences = list_from_form(form, "strong_preferences") or _merge_lists(
        territorial_preferences,
        protected_categories,
    )
    soft_preferences = list_from_form(form, "soft_preferences") or _merge_lists(
        target_roles,
        skills + technical_skills,
    )
    now = datetime.now().isoformat(timespec="minutes")
    conn.execute(
        """
        UPDATE profile
           SET professional_full_name = ?, professional_headline = ?,
               education = ?, education_items = ?, experiences = ?, certifications = ?,
               location_preference = ?, territorial_preferences = ?, availability = ?,
               protected_category_notes = ?, protected_categories = ?,
               strong_preferences = ?, soft_preferences = ?, skills = ?, technical_skills = ?,
               target_roles = ?, profile_notes = ?, profile_updated_at = ?,
               profile_schema_version = ?
         WHERE id = 1
        """,
        (
            form.get("professional_full_name", "").strip(),
            form.get("professional_headline", "").strip(),
            join_lines(education_items),
            _dump_json_list(education_items),
            _dump_json_list(experiences),
            _dump_json_list(certifications),
            join_lines(territorial_preferences),
            _dump_json_list(territorial_preferences),
            form.get("availability", "").strip(),
            join_lines(protected_categories),
            _dump_json_list(protected_categories),
            _dump_json_list(strong_preferences),
            _dump_json_list(soft_preferences),
            _dump_json_list(skills),
            _dump_json_list(technical_skills),
            _dump_json_list(target_roles),
            form.get("profile_notes", "").strip(),
            now,
            PROFILE_SCHEMA_VERSION,
        ),
    )


def profile_keywords(professional_profile):
    """Restituisce parole chiave ordinate per ranking, CV Manager e Radar AI."""
    keywords = []
    for key in (
        "target_roles",
        "skills",
        "technical_skills",
        "certifications",
        "education_items",
        "experiences",
        "territorial_preferences",
        "protected_categories",
        "strong_preferences",
        "soft_preferences",
    ):
        for value in professional_profile.get(key, []):
            if value and value not in keywords:
                keywords.append(value)
    return keywords
