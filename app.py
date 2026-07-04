"""
Radar Lavoro - aggregatore personale di offerte.

App Flask locale, monoutente, con database SQLite sul PC dell'utente.
Avvio: python app.py
Poi apri http://127.0.0.1:5000
"""

import hashlib
import json
import math
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import requests
from flask import Flask, flash, redirect, render_template, request, url_for

from radar_candidates import (
    APPLICATION_STATUS_OPTIONS,
    enrich_job_for_application,
    split_jobs_by_application_status,
    update_application,
)
from radar_cv import (
    CV_CATEGORIES,
    CV_FORMAT_OPTIONS,
    delete_cv,
    ensure_cv_schema,
    find_best_cv,
    load_cv,
    save_cv,
    set_default_cv,
)
from radar_documents import (
    DOCUMENT_CATEGORIES,
    DOCUMENT_FORMAT_OPTIONS,
    DOCUMENT_STATUS_OPTIONS,
    archive_document,
    delete_document,
    document_stats,
    ensure_document_schema,
    load_documents,
    save_document,
)
from radar_profile import (
    ensure_professional_profile_columns,
    join_lines,
    load_professional_profile,
    profile_keywords,
    save_professional_profile,
    seed_professional_profile,
)

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "radar_lavoro.db"
JOOBLE_URL = "https://it.jooble.org/api/{key}"

DEFAULT_QUERIES = [
    "comunicazione digitale",
    "social media manager",
    "content creator",
    "copywriter",
    "giornalista redattore",
    "ufficio stampa",
    "data analyst junior",
    "web developer junior",
]
DEFAULT_EXCLUDE = [
    "cameriere", "cuoco", "magazziniere", "autista", "operaio",
    "commesso", "bagnino", "pulizie", "muratore", "idraulico",
    "elettricista", "infermiere", "OSS", "badante", "animatore",
    "animatrice", "animazione", "fotomodell", "ballerin", "casting",
    "hostess", "beauty consultant", "consulente di bellezza",
    "informatore scientifico", "informatore medico", "sales assistant",
    "addetto vendit", "addetta vendit", "store manager", "agente di commercio",
    "venditore", "rappresentante", "ragazze immagine", "operatrice", "reception",
    "modell", "district manager", "area manager contratti", "beauty",
    "agente plurimandatario", "agenti plurimandatari", "key account", "account manager",
    "commerciale", "vendite", "sales", "procacciatore", "rinnovabili", "fotovoltaico",
    "plc", "farmaceutico", "pharma", "bricolage", "ferramenta", "casalinghi",
]
PAROLE_TROPPO_GENERICHE = {
    "junior", "stage", "lavoro", "offerta", "addetto", "addetta", "azienda",
    "figura", "profilo", "risorsa", "cerca", "ricerca", "sede", "area",
}

DISTANCE_OPTIONS = {
    "": "Solo citta selezionata",
    "10": "Entro 10 km",
    "20": "Entro 20 km",
    "30": "Entro 30 km",
    "50": "Entro 50 km",
    "province": "Tutta la provincia",
    "region": "Tutta la regione",
}
WORK_MODE_OPTIONS = {"remote": "Da remoto", "hybrid": "Ibrido / misto", "onsite": "In presenza"}
EXPERIENCE_OPTIONS = {"internship": "Stage / tirocinio", "entry": "Junior / entry level", "mid": "Intermedio", "senior": "Senior"}
CONTRACT_OPTIONS = {
    "permanent": "Tempo indeterminato",
    "fixed_term": "Tempo determinato",
    "apprenticeship": "Apprendistato",
    "internship": "Stage / tirocinio",
    "freelance": "Freelance / collaborazione / P. IVA",
}
SCHEDULE_OPTIONS = {"full_time": "Full time", "part_time": "Part time", "flexible": "Flessibile"}
SALARY_OPTIONS = {"": "Nessun minimo", "20000": "Almeno 20.000 EUR", "25000": "Almeno 25.000 EUR", "30000": "Almeno 30.000 EUR", "35000": "Almeno 35.000 EUR"}
PROTECTED_OPTIONS = {"off": "Non filtrare", "only": "Mostra solo offerte L.68/99", "priority": "Dai priorita alle offerte L.68/99"}
ORGANIZATION_OPTIONS = {"none": "Nessuna preferenza", "large": "Preferisci aziende grandi", "pmi": "Preferisci PMI", "pa": "Preferisci Pubblica Amministrazione"}

CITY_COORDS = {
    "nocera inferiore": (40.7454, 14.6410), "nocera superiore": (40.7421, 14.6746),
    "pagani": (40.7410, 14.6140), "angri": (40.7382, 14.5708),
    "scafati": (40.7464, 14.5296), "sant antonio abate": (40.7212, 14.5405),
    "sant'antonio abate": (40.7212, 14.5405), "san marzano sul sarno": (40.7780, 14.5844),
    "san valentino torio": (40.7929, 14.6022), "sarno": (40.8104, 14.6194),
    "roccapiemonte": (40.7610, 14.6923), "castel san giorgio": (40.7817, 14.6990),
    "cava de tirreni": (40.7019, 14.7046), "cava de' tirreni": (40.7019, 14.7046),
    "pompei": (40.7460, 14.4977), "salerno": (40.6824, 14.7681),
    "pontecagnano faiano": (40.6435, 14.8730), "castellammare di stabia": (40.6954, 14.4806),
    "torre annunziata": (40.7537, 14.4527), "ottaviano": (40.8512, 14.4783),
    "napoli": (40.8518, 14.2681),
}
CITY_PROVINCES = {
    "salerno": "SA", "nocera inferiore": "SA", "nocera superiore": "SA", "pagani": "SA", "angri": "SA",
    "scafati": "SA", "sarno": "SA", "cava de tirreni": "SA", "cava de' tirreni": "SA",
    "pontecagnano faiano": "SA", "castel san giorgio": "SA", "roccapiemonte": "SA",
    "san marzano sul sarno": "SA", "san valentino torio": "SA",
    "pompei": "NA", "castellammare di stabia": "NA", "torre annunziata": "NA", "ottaviano": "NA", "napoli": "NA",
}

QUERY_PROFILES = {
    "comunicazione digitale": {"required_any": ["comunicaz", "digital", "marketing", "content", "social", "media", "grafica", "adv"], "bonus": ["comunicazione", "digital", "marketing", "content", "social", "adv", "campagne", "seo", "copy"]},
    "social media manager": {"required_any": ["social", "media", "instagram", "facebook", "tiktok", "community", "content", "creator"], "bonus": ["social", "media", "content", "community", "meta", "adv", "storytelling"], "negative": ["key account", "account manager", "commerciale", "sales", "vendite", "rappresentante"]},
    "content creator": {"required_any": ["content", "creator", "contenut", "video", "storytelling", "social"], "bonus": ["content", "creator", "contenuti", "video", "copy", "storytelling"]},
    "copywriter": {"required_any": ["copy", "copywriter", "redatt", "testi", "scrittura", "contenut"], "bonus": ["copy", "copywriter", "redazione", "testi", "scrittura", "seo"]},
    "giornalista redattore": {"required_any": ["giornal", "redatt", "redazione", "editor", "stampa"], "bonus": ["giornal", "redatt", "redazione", "editor", "stampa"]},
    "ufficio stampa": {"required_any": ["stampa", "press", "comunicaz", "media relation", "pr"], "bonus": ["stampa", "press", "comunicazione", "media", "pr"]},
    "data analyst junior": {"required_any": ["data", "analyst", "analista", "dati", "analytics", "report", "dashboard", "python", "sql"], "bonus": ["data", "analyst", "analytics", "dati", "python", "sql", "excel", "report"], "negative": ["agente", "plurimandatario", "bricolage", "ferramenta", "casalinghi", "commerciale", "sales"]},
    "web developer junior": {"required_any": ["developer", "svilupp", "programmat", "web", "python", "javascript", "html", "css", "wordpress", ".net", "java"], "bonus": ["developer", "sviluppatore", "web", "python", "javascript", "html", "css", "wordpress", ".net", "java"], "negative": ["plc", "pharma", "commerciale", "key account", "sales", "agente"]},
}
GLOBAL_NEGATIVE_TERMS = ["agente plurimandatario", "agenti plurimandatari", "key account", "commerciale", "sales", "procacciatore", "venditore", "vendite", "plc", "bricolage", "ferramenta", "casalinghi"]
CV_TERMS = ["comunicazione", "comunicazione digitale", "corporate communication", "social media", "content", "copywriting", "copywriter", "giornalismo", "redazione", "ufficio stampa", "digital marketing", "web analytics", "seo", "sem", "analytics", "data analyst", "python", "html", "css", "javascript", "wordpress", "figma", "canva", "linkedin", "meta ads"]

app = Flask(__name__)
app.secret_key = "radar-lavoro-uso-personale"


def normalize_location(location: str) -> str:
    return " ".join((location or "").strip().lower().split())


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_column(conn, table_name: str, column_name: str, column_definition: str):
    columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    if column_name not in [column["name"] for column in columns]:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")


def init_db():
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            location TEXT DEFAULT '',
            queries TEXT DEFAULT '[]',
            exclude_keywords TEXT DEFAULT '[]',
            jooble_api_key TEXT DEFAULT '',
            distance_km TEXT DEFAULT '',
            work_modes TEXT DEFAULT '[]',
            experience_levels TEXT DEFAULT '[]',
            contract_types TEXT DEFAULT '[]',
            schedule_types TEXT DEFAULT '[]',
            salary_min TEXT DEFAULT '',
            protected_categories_mode TEXT DEFAULT 'off',
            organization_preference TEXT DEFAULT 'none',
            priority_salary INTEGER DEFAULT 0,
            priority_protected INTEGER DEFAULT 0,
            priority_remote INTEGER DEFAULT 0,
            deduplicate_cross_sites INTEGER DEFAULT 1,
            compatibility_enabled INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            external_id TEXT UNIQUE,
            canonical_key TEXT,
            title TEXT,
            company TEXT,
            location TEXT,
            search_location TEXT,
            snippet TEXT,
            link TEXT,
            updated TEXT,
            matched_query TEXT,
            compatibility_score INTEGER DEFAULT 0,
            priority_reasons TEXT DEFAULT '[]',
            status TEXT DEFAULT 'nuovo',
            application_status TEXT DEFAULT 'nuovo',
            personal_notes TEXT DEFAULT '',
            applied_at TEXT DEFAULT '',
            last_status_at TEXT DEFAULT '',
            first_seen_at TEXT
        );
        """
    )
    for column, definition in [
        ("distance_km", "TEXT DEFAULT ''"), ("work_modes", "TEXT DEFAULT '[]'"),
        ("experience_levels", "TEXT DEFAULT '[]'"), ("contract_types", "TEXT DEFAULT '[]'"),
        ("schedule_types", "TEXT DEFAULT '[]'"), ("salary_min", "TEXT DEFAULT ''"),
        ("protected_categories_mode", "TEXT DEFAULT 'off'"), ("organization_preference", "TEXT DEFAULT 'none'"),
        ("priority_salary", "INTEGER DEFAULT 0"), ("priority_protected", "INTEGER DEFAULT 0"),
        ("priority_remote", "INTEGER DEFAULT 0"), ("deduplicate_cross_sites", "INTEGER DEFAULT 1"),
        ("compatibility_enabled", "INTEGER DEFAULT 1"),
    ]:
        ensure_column(conn, "profile", column, definition)
    ensure_professional_profile_columns(conn, ensure_column)
    for column, definition in [
        ("search_location", "TEXT"), ("canonical_key", "TEXT"),
        ("compatibility_score", "INTEGER DEFAULT 0"), ("priority_reasons", "TEXT DEFAULT '[]'"),
        ("application_status", "TEXT DEFAULT 'nuovo'"), ("personal_notes", "TEXT DEFAULT ''"),
        ("applied_at", "TEXT DEFAULT ''"), ("last_status_at", "TEXT DEFAULT ''"),
    ]:
        ensure_column(conn, "jobs", column, definition)
    ensure_cv_schema(conn, ensure_column)
    ensure_document_schema(conn, ensure_column)
    conn.execute(
        """
        UPDATE jobs
           SET application_status = COALESCE(NULLIF(status, ''), 'nuovo')
         WHERE application_status IS NULL OR application_status = ''
        """
    )
    row = conn.execute("SELECT id FROM profile WHERE id = 1").fetchone()
    if row is None:
        conn.execute(
            """INSERT INTO profile
               (id, location, queries, exclude_keywords, distance_km, work_modes,
                experience_levels, contract_types, schedule_types, salary_min,
                protected_categories_mode, organization_preference, priority_salary,
                priority_protected, priority_remote, deduplicate_cross_sites, compatibility_enabled)
               VALUES (1, ?, ?, ?, '', '[]', '[]', '[]', '[]', '', 'off', 'none', 0, 1, 1, 1, 1)""",
            ("", json.dumps(DEFAULT_QUERIES), json.dumps(DEFAULT_EXCLUDE)),
        )
    seed_professional_profile(conn)
    conn.commit()
    conn.close()


def load_json_list(value):
    try:
        parsed = json.loads(value or "[]")
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def get_profile():
    conn = get_db()
    row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    professional_profile = load_professional_profile(conn)
    conn.close()
    return {
        "location": row["location"], "search_location": normalize_location(row["location"]),
        "queries": load_json_list(row["queries"]), "exclude_keywords": load_json_list(row["exclude_keywords"]),
        "jooble_api_key": row["jooble_api_key"], "distance_km": row["distance_km"] or "",
        "work_modes": load_json_list(row["work_modes"]), "experience_levels": load_json_list(row["experience_levels"]),
        "contract_types": load_json_list(row["contract_types"]), "schedule_types": load_json_list(row["schedule_types"]),
        "salary_min": row["salary_min"] or "", "protected_categories_mode": row["protected_categories_mode"] or "off",
        "organization_preference": row["organization_preference"] or "none",
        "priority_salary": bool(row["priority_salary"]), "priority_protected": bool(row["priority_protected"]),
        "priority_remote": bool(row["priority_remote"]), "deduplicate_cross_sites": bool(row["deduplicate_cross_sites"]),
        "compatibility_enabled": bool(row["compatibility_enabled"]),
        "professional_profile": professional_profile,
        "profile_keywords": profile_keywords(professional_profile),
        "distance_options": DISTANCE_OPTIONS, "work_mode_options": WORK_MODE_OPTIONS,
        "experience_options": EXPERIENCE_OPTIONS, "contract_options": CONTRACT_OPTIONS,
        "schedule_options": SCHEDULE_OPTIONS, "salary_options": SALARY_OPTIONS,
        "protected_options": PROTECTED_OPTIONS, "organization_options": ORGANIZATION_OPTIONS,
    }


def save_search_settings(location, queries, exclude_keywords, jooble_api_key, distance_km):
    conn = get_db()
    conn.execute(
        """UPDATE profile SET location=?, queries=?, exclude_keywords=?, jooble_api_key=?, distance_km=? WHERE id=1""",
        (location, json.dumps(queries), json.dumps(exclude_keywords), jooble_api_key, distance_km),
    )
    conn.commit()
    conn.close()


def save_advanced_filters(work_modes, experience_levels, contract_types, schedule_types,
                          salary_min, protected_categories_mode, organization_preference,
                          priority_salary, priority_protected, priority_remote,
                          deduplicate_cross_sites, compatibility_enabled):
    conn = get_db()
    conn.execute(
        """UPDATE profile
           SET work_modes=?, experience_levels=?, contract_types=?, schedule_types=?, salary_min=?,
               protected_categories_mode=?, organization_preference=?, priority_salary=?, priority_protected=?,
               priority_remote=?, deduplicate_cross_sites=?, compatibility_enabled=? WHERE id=1""",
        (json.dumps(work_modes), json.dumps(experience_levels), json.dumps(contract_types), json.dumps(schedule_types),
         salary_min, protected_categories_mode, organization_preference, int(priority_salary), int(priority_protected),
         int(priority_remote), int(deduplicate_cross_sites), int(compatibility_enabled)),
    )
    conn.commit()
    conn.close()


def testo_annuncio(job: dict) -> str:
    return " ".join([job.get("title") or "", job.get("company") or "", job.get("location") or "", job.get("snippet") or ""]).lower()


def contains_any(text: str, terms: list) -> bool:
    return any(term in text for term in terms)


def normalizza_testo(value: str) -> str:
    value = (value or "").lower()
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"[^a-z0-9àèéìòù]+", " ", value)
    return " ".join(value.split())


def canonical_job_key(job: dict) -> str:
    company = normalizza_testo(job.get("company") or "")
    title = normalizza_testo(job.get("title") or "")
    title = re.sub(r"\b(junior|senior|middle|full time|part time|orario flessibile|smart working)\b", " ", title)
    title = " ".join(title.split())
    base = f"{company}|{title}"
    if not company and not title:
        base = job.get("link") or ""
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def extract_city(location: str) -> str:
    text = normalizza_testo(location)
    if not text:
        return ""
    for city in sorted(CITY_COORDS.keys(), key=len, reverse=True):
        if city in text:
            return city
    text = re.sub(r"\b(sa|na|av|bn|ce)\b", " ", text)
    return " ".join(text.split()[:3])


def distance_km_between(city_a: str, city_b: str) -> float | None:
    a = CITY_COORDS.get(city_a)
    b = CITY_COORDS.get(city_b)
    if not a or not b:
        return None
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def matches_geo(job: dict, profile: dict) -> bool:
    search_city = extract_city(profile["location"])
    job_city = extract_city(job.get("location") or "")
    radius = profile["distance_km"]
    if not search_city or not job_city:
        return True
    if radius == "region":
        return True
    if radius == "province":
        return CITY_PROVINCES.get(search_city) == CITY_PROVINCES.get(job_city)
    if radius == "":
        return job_city == search_city
    try:
        max_distance = float(radius)
    except ValueError:
        return True
    distance = distance_km_between(search_city, job_city)
    if distance is None:
        return job_city == search_city
    return distance <= max_distance


def relevance_score(job: dict, query: str) -> int:
    text = testo_annuncio(job)
    title = normalizza_testo(job.get("title") or "")
    query_profile = QUERY_PROFILES.get(query.lower())
    if not query_profile:
        query_terms = [w for w in normalizza_testo(query).split() if len(w) > 3 and w not in PAROLE_TROPPO_GENERICHE]
        return sum(20 for term in query_terms if term in title or term in text)
    negative_hits = sum(1 for term in query_profile.get("negative", []) + GLOBAL_NEGATIVE_TERMS if term in text)
    if negative_hits:
        return max(0, 25 - negative_hits * 25)
    required_hits = sum(1 for term in query_profile["required_any"] if term in text)
    bonus_hits = sum(1 for term in query_profile.get("bonus", []) if term in text)
    title_hits = sum(1 for term in query_profile["required_any"] if term in title)
    if required_hits == 0:
        return 0
    return min(100, required_hits * 18 + bonus_hits * 6 + title_hits * 12)


def is_relevant(job: dict, query: str, exclude_keywords: list) -> bool:
    text = testo_annuncio(job)
    title = (job.get("title") or "").lower()
    if any(bad.lower() in title or bad.lower() in text for bad in exclude_keywords):
        return False
    return relevance_score(job, query) >= 35


def is_protected_category(job: dict) -> bool:
    text = testo_annuncio(job)
    return contains_any(text, ["legge 68/99", "l.68/99", "l 68/99", "68/99", "categorie protette", "categoria protetta", "invalidità civile", "invalidita civile", "disabili", "disabilità", "disabilita", "protected categories", "disability"])


def has_salary(job: dict) -> bool:
    text = testo_annuncio(job)
    return any(marker in text for marker in ["€", "eur", "ral", "stipendio", "retribuzione", "salary", "lordi", "netti"])


def is_remote(job: dict) -> bool:
    return contains_any(testo_annuncio(job), ["remoto", "remote", "smart working", "telelavoro", "home working", "da casa"])


def organization_type(job: dict) -> str:
    text = testo_annuncio(job)
    if contains_any(text, ["comune", "ministero", "università", "universita", "asl", "azienda sanitaria", "regione", "provincia", "ente pubblico", "pubblica amministrazione"]):
        return "pa"
    if contains_any(text, ["spa", "s.p.a", "multinazionale", "corporate", "group", "gruppo", "holding", "enterprise", "global", "accenture", "deloitte", "ey", "kpmg", "pwc", "telecom", "tim", "poste italiane", "intesa", "unicredit"]):
        return "large"
    if contains_any(text, ["srl", "s.r.l", "studio", "agenzia", "startup", "start up", "piccola", "media impresa", "pmi"]):
        return "pmi"
    return "unknown"


def matches_work_modes(job: dict, selected_modes: list) -> bool:
    if not selected_modes:
        return True
    terms = {"remote": ["remoto", "remote", "smart working", "telelavoro", "home working", "da casa"], "hybrid": ["ibrido", "ibrida", "hybrid", "misto", "mista", "parzialmente da remoto"], "onsite": ["in sede", "in presenza", "on site", "onsite", "ufficio", "sede di lavoro"]}
    text = testo_annuncio(job)
    return any(contains_any(text, terms.get(mode, [])) for mode in selected_modes)


def matches_experience_levels(job: dict, selected_levels: list) -> bool:
    if not selected_levels:
        return True
    terms = {"internship": ["stage", "tirocinio", "internship", "stagista", "curriculare", "extracurriculare"], "entry": ["junior", "entry level", "neolaureato", "neolaureata", "apprendistato", "prima esperienza"], "mid": ["middle", "intermedio", "2 anni", "3 anni", "esperienza pregressa", "specialist"], "senior": ["senior", "lead", "responsabile", "coordinator", "coordinatore", "5 anni"]}
    text = testo_annuncio(job)
    return any(contains_any(text, terms.get(level, [])) for level in selected_levels)


def matches_contract_types(job: dict, selected_contracts: list) -> bool:
    if not selected_contracts:
        return True
    terms = {"permanent": ["tempo indeterminato", "indeterminato", "permanent"], "fixed_term": ["tempo determinato", "determinato", "fixed term"], "apprenticeship": ["apprendistato", "apprenticeship"], "internship": ["stage", "tirocinio", "internship"], "freelance": ["freelance", "collaborazione", "partita iva", "p. iva", "p iva", "consulenza"]}
    text = testo_annuncio(job)
    return any(contains_any(text, terms.get(contract, [])) for contract in selected_contracts)


def matches_schedule_types(job: dict, selected_schedules: list) -> bool:
    if not selected_schedules:
        return True
    terms = {"full_time": ["full time", "full-time", "tempo pieno"], "part_time": ["part time", "part-time", "tempo parziale"], "flexible": ["flessibile", "orario flessibile", "smart working", "da remoto"]}
    text = testo_annuncio(job)
    return any(contains_any(text, terms.get(schedule, [])) for schedule in selected_schedules)


def matches_salary(job: dict, salary_min: str) -> bool:
    if not salary_min:
        return True
    text = testo_annuncio(job)
    if not has_salary(job):
        return True
    return salary_min in text or f"{int(salary_min) // 1000}k" in text


def passes_filters(job: dict, profile: dict, query: str) -> bool:
    if not matches_geo(job, profile):
        return False
    if profile["protected_categories_mode"] == "only" and not is_protected_category(job):
        return False
    return (
        is_relevant(job, query, profile["exclude_keywords"])
        and matches_work_modes(job, profile["work_modes"])
        and matches_experience_levels(job, profile["experience_levels"])
        and matches_contract_types(job, profile["contract_types"])
        and matches_schedule_types(job, profile["schedule_types"])
        and matches_salary(job, profile["salary_min"])
    )


def compatibility_score(job: dict, keyword: str, profile: dict) -> tuple[int, list]:
    text = testo_annuncio(job)
    reasons = []
    relevance = relevance_score(job, keyword)
    score = min(45, int(relevance * 0.45))
    if relevance >= 60:
        reasons.append("molto pertinente")
    elif relevance >= 35:
        reasons.append("pertinente")
    profile_terms = profile_keywords(profile.get("professional_profile", {})) or CV_TERMS
    matched_terms = [term for term in profile_terms if term.lower() in text]
    score += min(25, len(matched_terms) * 4)
    if matched_terms:
        reasons.append("profilo coerente")
    if is_protected_category(job):
        score += 15 if profile["priority_protected"] or profile["protected_categories_mode"] == "priority" else 8
        reasons.append("categorie protette")
    if is_remote(job):
        score += 12 if profile["priority_remote"] else 6
        reasons.append("remoto")
    if has_salary(job):
        score += 8 if profile["priority_salary"] else 4
        reasons.append("stipendio indicato")
    org_pref = profile["organization_preference"]
    org_type = organization_type(job)
    if org_pref != "none" and org_pref == org_type:
        score += 8
        reasons.append(ORGANIZATION_OPTIONS.get(org_pref, "organizzazione preferita").lower())
    if matches_experience_levels(job, ["internship", "entry"]):
        score += 5
        reasons.append("adatto a profilo junior")
    return min(100, max(0, score)), reasons[:5]


def search_jooble(keyword: str, profile: dict) -> list:
    url = JOOBLE_URL.format(key=profile["jooble_api_key"])
    payload = {"keywords": keyword, "location": profile["location"]}
    if profile["distance_km"] and profile["distance_km"].isdigit():
        payload["radius"] = profile["distance_km"]
    try:
        resp = requests.post(url, json=payload, timeout=20)
        resp.raise_for_status()
        return resp.json().get("jobs", [])[:40]
    except requests.RequestException:
        return []


def refresh_jobs():
    profile = get_profile()
    if not profile["location"]:
        return 0, "Imposta prima la tua citta in Ricerca."
    if not profile["jooble_api_key"]:
        return 0, "Imposta prima la tua API key Jooble in Ricerca."
    if not profile["queries"]:
        return 0, "Aggiungi almeno una parola chiave di ricerca."
    conn = get_db()
    new_count = 0
    collected_jobs = []
    seen_canonical_keys = set()
    for keyword in profile["queries"]:
        for job in search_jooble(keyword, profile):
            link = job.get("link") or ""
            if not link:
                continue
            canonical_key = canonical_job_key(job)
            external_id = f"{profile['search_location']}|{link}"
            if not passes_filters(job, profile, keyword):
                continue
            if profile["deduplicate_cross_sites"] and canonical_key in seen_canonical_keys:
                continue
            seen_canonical_keys.add(canonical_key)
            exists = conn.execute("SELECT id FROM jobs WHERE external_id = ?", (external_id,)).fetchone()
            if exists:
                continue
            if profile["deduplicate_cross_sites"]:
                duplicate = conn.execute(
                    "SELECT id FROM jobs WHERE canonical_key = ? AND search_location = ?",
                    (canonical_key, profile["search_location"]),
                ).fetchone()
                if duplicate:
                    continue
            score, reasons = compatibility_score(job, keyword, profile) if profile["compatibility_enabled"] else (0, [])
            collected_jobs.append((score, reasons, keyword, canonical_key, external_id, job))
    collected_jobs.sort(key=lambda item: item[0], reverse=True)
    for score, reasons, keyword, canonical_key, external_id, job in collected_jobs:
        conn.execute(
            """INSERT INTO jobs (external_id, canonical_key, title, company, location, search_location,
               snippet, link, updated, matched_query, compatibility_score, priority_reasons, status, first_seen_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'nuovo', ?)""",
            (external_id, canonical_key, job.get("title") or "Senza titolo", job.get("company", "Azienda non specificata"),
             job.get("location", ""), profile["search_location"], (job.get("snippet") or "").replace("&nbsp;", " ").strip(),
             job.get("link") or "", job.get("updated", ""), keyword, score, json.dumps(reasons),
             datetime.now().isoformat(timespec="minutes")),
        )
        new_count += 1
    conn.commit()
    conn.close()
    return new_count, None


def row_to_job(row):
    job = dict(row)
    job["priority_reasons"] = load_json_list(job.get("priority_reasons"))
    return enrich_job_for_application(job)


@app.route("/")
def dashboard():
    profile = get_profile()
    conn = get_db()
    rows = conn.execute(
        """SELECT * FROM jobs WHERE search_location = ? ORDER BY compatibility_score DESC, first_seen_at DESC LIMIT 150""",
        (profile["search_location"],),
    ).fetchall()
    conn.close()
    filtered_jobs = []
    for row in rows:
        job = row_to_job(row)
        if passes_filters(job, profile, job.get("matched_query") or ""):
            filtered_jobs.append(job)
    nuovi, candidature, stats = split_jobs_by_application_status(filtered_jobs)
    return render_template(
        "dashboard.html",
        nuovi=nuovi,
        candidature=candidature,
        stats=stats,
        application_status_options=APPLICATION_STATUS_OPTIONS,
        profile=profile,
    )


@app.route("/aggiorna", methods=["POST"])
def aggiorna():
    count, error = refresh_jobs()
    if error:
        flash(error, "errore")
    else:
        flash(f"{count} nuovi annunci trovati, filtrati e ordinati per compatibilita.", "successo")
    return redirect(url_for("dashboard"))


@app.route("/candidatura/<int:job_id>", methods=["POST"])
def aggiorna_candidatura(job_id):
    profile = get_profile()
    conn = get_db()
    update_application(conn, job_id, profile["search_location"], request.form)
    conn.commit()
    conn.close()
    flash("Candidatura aggiornata.", "successo")
    return redirect(url_for("dashboard"))


@app.route("/segna-visto/<int:job_id>", methods=["POST"])
def segna_visto(job_id):
    profile = get_profile()
    conn = get_db()
    now = datetime.now().isoformat(timespec="minutes")
    conn.execute(
        """UPDATE jobs
              SET status = 'visto', application_status = 'visto', last_status_at = ?
            WHERE id = ? AND search_location = ?""",
        (now, job_id, profile["search_location"]),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))


@app.route("/segna-tutti-visti", methods=["POST"])
def segna_tutti_visti():
    profile = get_profile()
    conn = get_db()
    now = datetime.now().isoformat(timespec="minutes")
    conn.execute(
        """UPDATE jobs
              SET status = 'visto', application_status = 'visto', last_status_at = ?
            WHERE status = 'nuovo'
              AND COALESCE(NULLIF(application_status, ''), 'nuovo') = 'nuovo'
              AND search_location = ?""",
        (now, profile["search_location"]),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))


@app.route("/impostazioni", methods=["GET", "POST"])
def impostazioni():
    if request.method == "POST":
        location = request.form.get("location", "").strip()
        queries = [q.strip() for q in request.form.get("queries", "").split(",") if q.strip()]
        exclude = [q.strip() for q in request.form.get("exclude_keywords", "").split(",") if q.strip()]
        jooble_api_key = request.form.get("jooble_api_key", "").strip()
        distance_km = request.form.get("distance_km", "").strip()
        if distance_km not in DISTANCE_OPTIONS:
            distance_km = ""
        save_search_settings(location, queries, exclude, jooble_api_key, distance_km)
        flash("Ricerca salvata. Ora puoi premere Cerca ora dalla Dashboard.", "successo")
        return redirect(url_for("impostazioni"))
    return render_template("impostazioni.html", profile=get_profile())


@app.route("/filtri", methods=["GET", "POST"])
def filtri():
    if request.method == "POST":
        work_modes = [mode for mode in request.form.getlist("work_modes") if mode in WORK_MODE_OPTIONS]
        experience_levels = [level for level in request.form.getlist("experience_levels") if level in EXPERIENCE_OPTIONS]
        contract_types = [contract for contract in request.form.getlist("contract_types") if contract in CONTRACT_OPTIONS]
        schedule_types = [schedule for schedule in request.form.getlist("schedule_types") if schedule in SCHEDULE_OPTIONS]
        salary_min = request.form.get("salary_min", "").strip()
        protected_mode = request.form.get("protected_categories_mode", "off").strip()
        organization_preference = request.form.get("organization_preference", "none").strip()
        if salary_min not in SALARY_OPTIONS:
            salary_min = ""
        if protected_mode not in PROTECTED_OPTIONS:
            protected_mode = "off"
        if organization_preference not in ORGANIZATION_OPTIONS:
            organization_preference = "none"
        save_advanced_filters(
            work_modes, experience_levels, contract_types, schedule_types, salary_min, protected_mode,
            organization_preference, "priority_salary" in request.form, "priority_protected" in request.form,
            "priority_remote" in request.form, "deduplicate_cross_sites" in request.form,
            "compatibility_enabled" in request.form,
        )
        flash("Filtri e priorita salvati. Verranno applicati alla prossima ricerca.", "successo")
        return redirect(url_for("filtri"))
    return render_template("filtri.html", profile=get_profile())


@app.route("/profilo", methods=["GET", "POST"])
def profilo():
    conn = get_db()
    if request.method == "POST":
        save_professional_profile(conn, request.form)
        conn.commit()
        conn.close()
        flash("Profilo professionale salvato.", "successo")
        return redirect(url_for("profilo"))
    professional_profile = load_professional_profile(conn)
    conn.close()
    return render_template(
        "profilo.html",
        professional_profile=professional_profile,
        join_lines=join_lines,
    )


@app.route("/cv", methods=["GET", "POST"])
def cv_manager():
    conn = get_db()
    if request.method == "POST":
        raw_cv_id = request.form.get("cv_id", "").strip()
        cv_id = int(raw_cv_id) if raw_cv_id.isdigit() else None
        save_cv(conn, request.form, cv_id)
        conn.commit()
        conn.close()
        flash("CV aggiornato." if cv_id else "CV aggiunto.", "successo")
        return redirect(url_for("cv_manager"))

    edit_id = request.args.get("edit", type=int)
    edit_cv = load_cv(conn, edit_id) if edit_id else None
    if edit_id and edit_cv is None:
        conn.close()
        flash("CV non trovato.", "errore")
        return redirect(url_for("cv_manager"))

    cv_documents = load_cv(conn)
    suggested_cv = find_best_cv(conn)
    conn.close()
    return render_template(
        "cv.html",
        cv_documents=cv_documents,
        edit_cv=edit_cv,
        suggested_cv=suggested_cv,
        cv_categories=CV_CATEGORIES,
        cv_format_options=CV_FORMAT_OPTIONS,
    )


@app.route("/cv/<int:cv_id>/elimina", methods=["POST"])
def elimina_cv(cv_id):
    conn = get_db()
    deleted = delete_cv(conn, cv_id)
    conn.commit()
    conn.close()
    flash("CV eliminato dal manager." if deleted else "CV non trovato.", "successo" if deleted else "errore")
    return redirect(url_for("cv_manager"))


@app.route("/cv/<int:cv_id>/predefinito", methods=["POST"])
def imposta_cv_predefinito(cv_id):
    conn = get_db()
    updated = set_default_cv(conn, cv_id)
    conn.commit()
    conn.close()
    flash("CV impostato come predefinito." if updated else "CV non trovato.", "successo" if updated else "errore")
    return redirect(url_for("cv_manager"))


@app.route("/documenti", methods=["GET", "POST"])
def archivio_documenti():
    conn = get_db()
    if request.method == "POST":
        raw_document_id = request.form.get("document_id", "").strip()
        document_id = int(raw_document_id) if raw_document_id.isdigit() else None
        save_document(conn, request.form, document_id)
        conn.commit()
        conn.close()
        flash("Documento aggiornato." if document_id else "Documento aggiunto all'archivio.", "successo")
        return redirect(url_for("archivio_documenti"))

    edit_id = request.args.get("edit", type=int)
    edit_document = load_documents(conn, edit_id) if edit_id else None
    if edit_id and edit_document is None:
        conn.close()
        flash("Documento non trovato.", "errore")
        return redirect(url_for("archivio_documenti"))

    documents = load_documents(conn)
    cv_documents = load_cv(conn)
    stats = document_stats(documents)
    conn.close()
    return render_template(
        "documenti.html",
        documents=documents,
        edit_document=edit_document,
        cv_documents=cv_documents,
        stats=stats,
        document_categories=DOCUMENT_CATEGORIES,
        document_format_options=DOCUMENT_FORMAT_OPTIONS,
        document_status_options=DOCUMENT_STATUS_OPTIONS,
        join_lines=join_lines,
    )


@app.route("/documenti/<int:document_id>/elimina", methods=["POST"])
def elimina_documento(document_id):
    conn = get_db()
    deleted = delete_document(conn, document_id)
    conn.commit()
    conn.close()
    flash("Documento eliminato dall'archivio." if deleted else "Documento non trovato.", "successo" if deleted else "errore")
    return redirect(url_for("archivio_documenti"))


@app.route("/documenti/<int:document_id>/archivia", methods=["POST"])
def archivia_documento(document_id):
    conn = get_db()
    archived = archive_document(conn, document_id)
    conn.commit()
    conn.close()
    flash("Documento archiviato." if archived else "Documento non trovato.", "successo" if archived else "errore")
    return redirect(url_for("archivio_documenti"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
