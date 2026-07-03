"""
Modulo Profilo professionale per Radar Lavoro.

Gestisce il profilo unico dell'utente, separando le preferenze di carriera
forti da quelle leggere. Il modulo e pensato per essere usato dal ranking,
dalla pagina profilo e dai prossimi sprint CV Manager / Radar AI.
"""

import json
from datetime import datetime


DEFAULT_PROFILE = {
    "full_name": "Andrea Bartiromo",
    "headline": "Corporate Communication, Digital Marketing e contenuti digitali",
    "education": "Laurea Magistrale in Corporate Communication - Universita degli Studi di Salerno",
    "location_preference": "Provincia di Salerno, Agro Nocerino-Sarnese, remoto o ibrido quando possibile",
    "availability": "Part-time, stage, apprendistato o opportunita junior compatibili con il percorso universitario",
    "protected_category_notes": "Categorie protette L.68/99 - invalidita civile 75%",
    "strong_preferences": [
        "remoto o ibrido",
        "provincia di Salerno o Campania",
        "comunicazione digitale",
        "content creation",
        "ufficio stampa",
        "categorie protette L.68/99",
    ],
    "soft_preferences": [
        "digital marketing",
        "social media",
        "web analytics",
        "redazione contenuti",
        "pubblica amministrazione",
        "data analyst junior",
    ],
    "skills": [
        "comunicazione digitale",
        "corporate communication",
        "social media",
        "content writing",
        "copywriting",
        "giornalismo",
        "ufficio stampa",
        "digital marketing",
        "web analytics",
        "SEO",
        "SEM",
        "Canva",
        "Figma",
        "HTML",
        "CSS",
        "JavaScript",
        "Python base",
    ],
    "target_roles": [
        "Social Media Assistant",
        "Content Creator Junior",
        "Copywriter Junior",
        "Addetto comunicazione",
        "Ufficio stampa junior",
        "Digital Marketing Assistant",
        "Data Analyst Junior",
        "Operatore amministrativo categorie protette",
    ],
    "notes": "Profilo pensato per ordinare le opportunita in base alla reale utilita per Andrea.",
}

PROFILE_COLUMNS = {
    "professional_full_name": "TEXT DEFAULT ''",
    "professional_headline": "TEXT DEFAULT ''",
    "education": "TEXT DEFAULT ''",
    "location_preference": "TEXT DEFAULT ''",
    "availability": "TEXT DEFAULT ''",
    "protected_category_notes": "TEXT DEFAULT ''",
    "strong_preferences": "TEXT DEFAULT '[]'",
    "soft_preferences": "TEXT DEFAULT '[]'",
    "skills": "TEXT DEFAULT '[]'",
    "target_roles": "TEXT DEFAULT '[]'",
    "profile_notes": "TEXT DEFAULT ''",
    "profile_updated_at": "TEXT DEFAULT ''",
}


def _load_json_list(value):
    try:
        parsed = json.loads(value or "[]")
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def split_lines(value):
    return [line.strip() for line in (value or "").splitlines() if line.strip()]


def join_lines(values):
    return "\n".join(values or [])


def ensure_professional_profile_columns(conn, ensure_column):
    """Aggiunge le colonne del profilo alla tabella profile senza perdere dati."""
    for column_name, column_definition in PROFILE_COLUMNS.items():
        ensure_column(conn, "profile", column_name, column_definition)


def seed_professional_profile(conn):
    """Compila il profilo iniziale solo se non e gia stato personalizzato."""
    row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    if row is None:
        return
    if row["professional_full_name"]:
        return
    now = datetime.now().isoformat(timespec="minutes")
    conn.execute(
        """
        UPDATE profile
           SET professional_full_name = ?, professional_headline = ?, education = ?,
               location_preference = ?, availability = ?, protected_category_notes = ?,
               strong_preferences = ?, soft_preferences = ?, skills = ?, target_roles = ?,
               profile_notes = ?, profile_updated_at = ?
         WHERE id = 1
        """,
        (
            DEFAULT_PROFILE["full_name"],
            DEFAULT_PROFILE["headline"],
            DEFAULT_PROFILE["education"],
            DEFAULT_PROFILE["location_preference"],
            DEFAULT_PROFILE["availability"],
            DEFAULT_PROFILE["protected_category_notes"],
            json.dumps(DEFAULT_PROFILE["strong_preferences"], ensure_ascii=False),
            json.dumps(DEFAULT_PROFILE["soft_preferences"], ensure_ascii=False),
            json.dumps(DEFAULT_PROFILE["skills"], ensure_ascii=False),
            json.dumps(DEFAULT_PROFILE["target_roles"], ensure_ascii=False),
            DEFAULT_PROFILE["notes"],
            now,
        ),
    )


def profile_from_row(row):
    return {
        "professional_full_name": row["professional_full_name"] or DEFAULT_PROFILE["full_name"],
        "professional_headline": row["professional_headline"] or DEFAULT_PROFILE["headline"],
        "education": row["education"] or DEFAULT_PROFILE["education"],
        "location_preference": row["location_preference"] or DEFAULT_PROFILE["location_preference"],
        "availability": row["availability"] or DEFAULT_PROFILE["availability"],
        "protected_category_notes": row["protected_category_notes"] or DEFAULT_PROFILE["protected_category_notes"],
        "strong_preferences": _load_json_list(row["strong_preferences"]),
        "soft_preferences": _load_json_list(row["soft_preferences"]),
        "skills": _load_json_list(row["skills"]),
        "target_roles": _load_json_list(row["target_roles"]),
        "profile_notes": row["profile_notes"] or "",
        "profile_updated_at": row["profile_updated_at"] or "",
    }


def load_professional_profile(conn):
    row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    if row is None:
        return DEFAULT_PROFILE.copy()
    return profile_from_row(row)


def save_professional_profile(conn, form):
    now = datetime.now().isoformat(timespec="minutes")
    conn.execute(
        """
        UPDATE profile
           SET professional_full_name = ?, professional_headline = ?, education = ?,
               location_preference = ?, availability = ?, protected_category_notes = ?,
               strong_preferences = ?, soft_preferences = ?, skills = ?, target_roles = ?,
               profile_notes = ?, profile_updated_at = ?
         WHERE id = 1
        """,
        (
            form.get("professional_full_name", "").strip(),
            form.get("professional_headline", "").strip(),
            form.get("education", "").strip(),
            form.get("location_preference", "").strip(),
            form.get("availability", "").strip(),
            form.get("protected_category_notes", "").strip(),
            json.dumps(split_lines(form.get("strong_preferences", "")), ensure_ascii=False),
            json.dumps(split_lines(form.get("soft_preferences", "")), ensure_ascii=False),
            json.dumps(split_lines(form.get("skills", "")), ensure_ascii=False),
            json.dumps(split_lines(form.get("target_roles", "")), ensure_ascii=False),
            form.get("profile_notes", "").strip(),
            now,
        ),
    )


def profile_keywords(professional_profile):
    """Restituisce parole chiave ordinate per uso futuro nel ranking e nel CV Manager."""
    keywords = []
    for key in ("target_roles", "skills", "strong_preferences", "soft_preferences"):
        for value in professional_profile.get(key, []):
            if value and value not in keywords:
                keywords.append(value)
    return keywords
