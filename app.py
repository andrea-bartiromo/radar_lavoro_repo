"""Radar Lavoro — applicazione Flask personale.

Avvio locale:
    python app.py

Poi apri:
    http://127.0.0.1:5000
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from flask import Flask, flash, redirect, render_template, request, url_for

from services.filter_service import (
    matches_contract_types,
    matches_experience_levels,
    matches_schedule_types,
    matches_work_modes,
)
from services.geo_service import is_within_search_area
from services.profile_service import get_personal_profile, get_profile_matching_terms
from services.text_service import build_job_text, contains_any, normalize_text, split_comma_values

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
    "cameriere",
    "cuoco",
    "magazziniere",
    "autista",
    "operaio",
    "commesso",
    "bagnino",
    "pulizie",
    "muratore",
    "idraulico",
    "elettricista",
    "infermiere",
    "oss",
    "badante",
    "animatore",
    "animatrice",
    "animazione",
    "fotomodell",
    "ballerin",
    "casting",
    "hostess",
    "beauty consultant",
    "consulente di bellezza",
    "informatore scientifico",
    "informatore medico",
    "sales assistant",
    "addetto vendit",
    "addetta vendit",
    "store manager",
    "agente di commercio",
    "venditore",
    "rappresentante",
    "ragazze immagine",
    "operatrice",
    "reception",
    "modell",
    "district manager",
    "area manager contratti",
    "beauty",
    "agente plurimandatario",
    "agenti plurimandatari",
    "key account",
    "account manager",
    "commerciale",
    "vendite",
    "sales",
    "procacciatore",
    "rinnovabili",
    "fotovoltaico",
    "plc",
    "farmaceutico",
    "pharma",
    "bricolage",
    "ferramenta",
    "casalinghi",
    "brevetti",
    "patent attorney",
    "mandatario brevetti",
    "telemarketing",
    "call center",
]

DISTANCE_OPTIONS = {
    "": "Solo città selezionata",
    "10": "Entro 10 km",
    "20": "Entro 20 km",
    "30": "Entro 30 km",
    "50": "Entro 50 km",
    "province": "Tutta la provincia",
    "region": "Tutta la regione",
}

WORK_MODE_OPTIONS = {
    "remote": "Da remoto",
    "hybrid": "Ibrido / misto",
    "onsite": "In presenza",
}

EXPERIENCE_OPTIONS = {
    "internship": "Stage / tirocinio",
    "entry": "Junior / entry level",
    "mid": "Intermedio",
    "senior": "Senior",
}

CONTRACT_OPTIONS = {
    "permanent": "Tempo indeterminato",
    "fixed_term": "Tempo determinato",
    "apprenticeship": "Apprendistato",
    "internship": "Stage / tirocinio",
    "freelance": "Freelance / collaborazione / P. IVA",
}

SCHEDULE_OPTIONS = {
    "full_time": "Full time",
    "part_time": "Part time",
    "flexible": "Flessibile",
}

SALARY_OPTIONS = {
    "": "Nessun minimo",
    "20000": "Almeno 20.000 €",
    "25000": "Almeno 25.000 €",
    "30000": "Almeno 30.000 €",
    "35000": "Almeno 35.000 €",
}

PROTECTED_OPTIONS = {
    "off": "Non filtrare",
    "only": "Mostra solo offerte L.68/99",
    "priority": "Dai priorità alle offerte L.68/99",
}

ORGANIZATION_OPTIONS = {
    "none": "Nessuna preferenza",
    "large": "Preferisci aziende grandi",
    "pmi": "Preferisci PMI",
    "pa": "Preferisci Pubblica Amministrazione",
}

HARD_BLOCK_TERMS = [
    "patent attorney",
    "mandatario brevetti",
    "brevetti",
    "agente plurimandatario",
    "ragazze immagine",
    "fotomodell",
    "casting",
    "call center",
    "telemarketing",
    "operatore outbound",
]

GLOBAL_NEGATIVE_TERMS = [
    "agente plurimandatario",
    "agenti plurimandatari",
    "key account",
    "procacciatore",
    "plc",
    "bricolage",
    "ferramenta",
    "casalinghi",
    "patent attorney",
    "mandatario brevetti",
    "brevetti",
    "telemarketing",
    "call center",
    "operatore outbound",
]

ENTRY_TERMS = [
    "junior",
    "stage",
    "tirocinio",
    "entry level",
    "neolaureato",
    "neolaureata",
    "apprendistato",
    "prima esperienza",
]

SENIOR_TERMS = [
    "senior",
    "lead",
    "responsabile",
    "head of",
    "coordinator",
    "coordinatore",
    "manager",
    "team lead",
]

QUERY_PROFILES = {
    "comunicazione digitale": {
        "positive": [
            "comunicaz",
            "digital",
            "marketing",
            "content",
            "social",
            "media",
            "grafica",
            "adv",
            "seo",
            "copy",
        ],
        "strong": [
            "comunicazione",
            "digital marketing",
            "social media",
            "content",
            "ufficio stampa",
            "seo",
            "copy",
        ],
        "negative": ["telemarketing", "call center", "outbound", "vendite", "sales"],
    },
    "social media manager": {
        "positive": [
            "social",
            "media",
            "instagram",
            "facebook",
            "tiktok",
            "community",
            "content",
            "creator",
            "meta",
        ],
        "strong": ["social media", "community", "instagram", "facebook", "tiktok", "meta"],
        "negative": ["key account", "commerciale", "sales", "vendite", "telemarketing"],
    },
    "content creator": {
        "positive": ["content", "creator", "contenut", "video", "storytelling", "social"],
        "strong": ["content creator", "contenuti", "storytelling", "social"],
        "negative": ["ragazza", "ragazze immagine", "casting", "fotomodell"],
    },
    "copywriter": {
        "positive": ["copy", "copywriter", "redatt", "testi", "scrittura", "contenut"],
        "strong": ["copywriter", "redattore", "redattrice", "testi", "scrittura"],
        "negative": [],
    },
    "giornalista redattore": {
        "positive": ["giornal", "redatt", "redazione", "editor", "stampa"],
        "strong": ["giornalista", "redattore", "redattrice", "redazione", "editor"],
        "negative": [],
    },
    "ufficio stampa": {
        "positive": ["stampa", "press", "comunicaz", "media relation", "pr"],
        "strong": ["ufficio stampa", "press", "media relation", "pr", "comunicazione"],
        "negative": [],
    },
    "data analyst junior": {
        "positive": [
            "data",
            "analyst",
            "analista",
            "dati",
            "analytics",
            "report",
            "dashboard",
            "python",
            "sql",
            "excel",
        ],
        "strong": [
            "data analyst",
            "analista dati",
            "business analyst",
            "analytics",
            "python",
            "sql",
            "dashboard",
            "report",
        ],
        "negative": [
            "agente",
            "plurimandatario",
            "commerciale",
            "brevetti",
            "patent",
            "attorney",
            "mandatario",
            "meccatronica",
            "elettronica",
        ],
    },
    "web developer junior": {
        "positive": [
            "developer",
            "svilupp",
            "programmat",
            "web",
            "python",
            "javascript",
            "html",
            "css",
            "wordpress",
            ".net",
            "java",
            "software",
        ],
        "strong": [
            "web developer",
            "software developer",
            "sviluppatore",
            "developer",
            "programmatore",
            "python",
            "javascript",
            ".net",
            "java",
            "wordpress",
        ],
        "negative": ["plc", "pharma", "commerciale", "key account", "sales", "agente"],
    },
}

app = Flask(__name__)
app.secret_key = "radar-lavoro-uso-personale"


@dataclass(frozen=True)
class SearchStats:
    raw: int = 0
    geo_rejected: int = 0
    relevance_rejected: int = 0
    duplicate_rejected: int = 0
    saved: int = 0


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def load_json_list(value: str | None) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []

    return parsed if isinstance(parsed, list) else []


def ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = conn.execute(f"PRAGMA table_info({table})").fetchall()
    column_names = [row["name"] for row in columns]

    if column not in column_names:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db() -> None:
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
            first_seen_at TEXT
        );
        """
    )

    profile_columns = {
        "distance_km": "TEXT DEFAULT ''",
        "work_modes": "TEXT DEFAULT '[]'",
        "experience_levels": "TEXT DEFAULT '[]'",
        "contract_types": "TEXT DEFAULT '[]'",
        "schedule_types": "TEXT DEFAULT '[]'",
        "salary_min": "TEXT DEFAULT ''",
        "protected_categories_mode": "TEXT DEFAULT 'off'",
        "organization_preference": "TEXT DEFAULT 'none'",
        "priority_salary": "INTEGER DEFAULT 0",
        "priority_protected": "INTEGER DEFAULT 0",
        "priority_remote": "INTEGER DEFAULT 0",
        "deduplicate_cross_sites": "INTEGER DEFAULT 1",
        "compatibility_enabled": "INTEGER DEFAULT 1",
    }

    job_columns = {
        "search_location": "TEXT",
        "canonical_key": "TEXT",
        "compatibility_score": "INTEGER DEFAULT 0",
        "priority_reasons": "TEXT DEFAULT '[]'",
    }

    for column, definition in profile_columns.items():
        ensure_column(conn, "profile", column, definition)

    for column, definition in job_columns.items():
        ensure_column(conn, "jobs", column, definition)

    row = conn.execute("SELECT id FROM profile WHERE id = 1").fetchone()
    if row is None:
        conn.execute(
            """
            INSERT INTO profile (
                id,
                location,
                queries,
                exclude_keywords,
                distance_km,
                work_modes,
                experience_levels,
                contract_types,
                schedule_types,
                salary_min,
                protected_categories_mode,
                organization_preference,
                priority_salary,
                priority_protected,
                priority_remote,
                deduplicate_cross_sites,
                compatibility_enabled
            )
            VALUES (1, ?, ?, ?, '', '[]', '[]', '[]', '[]', '', 'off', 'none', 0, 1, 1, 1, 1)
            """,
            ("", json.dumps(DEFAULT_QUERIES), json.dumps(DEFAULT_EXCLUDE)),
        )

    conn.commit()
    conn.close()


def normalize_location(location: str) -> str:
    return " ".join((location or "").strip().lower().split())


def get_profile() -> dict[str, Any]:
    conn = get_db()
    row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    conn.close()

    return {
        "location": row["location"],
        "search_location": normalize_location(row["location"]),
        "queries": load_json_list(row["queries"]),
        "exclude_keywords": load_json_list(row["exclude_keywords"]),
        "jooble_api_key": row["jooble_api_key"],
        "distance_km": row["distance_km"] or "",
        "work_modes": load_json_list(row["work_modes"]),
        "experience_levels": load_json_list(row["experience_levels"]),
        "contract_types": load_json_list(row["contract_types"]),
        "schedule_types": load_json_list(row["schedule_types"]),
        "salary_min": row["salary_min"] or "",
        "protected_categories_mode": row["protected_categories_mode"] or "off",
        "organization_preference": row["organization_preference"] or "none",
        "priority_salary": bool(row["priority_salary"]),
        "priority_protected": bool(row["priority_protected"]),
        "priority_remote": bool(row["priority_remote"]),
        "deduplicate_cross_sites": bool(row["deduplicate_cross_sites"]),
        "compatibility_enabled": bool(row["compatibility_enabled"]),
        "distance_options": DISTANCE_OPTIONS,
        "work_mode_options": WORK_MODE_OPTIONS,
        "experience_options": EXPERIENCE_OPTIONS,
        "contract_options": CONTRACT_OPTIONS,
        "schedule_options": SCHEDULE_OPTIONS,
        "salary_options": SALARY_OPTIONS,
        "protected_options": PROTECTED_OPTIONS,
        "organization_options": ORGANIZATION_OPTIONS,
    }


def save_search_settings(
    location: str,
    queries: list[str],
    exclude_keywords: list[str],
    jooble_api_key: str,
    distance_km: str,
) -> None:
    conn = get_db()
    conn.execute(
        """
        UPDATE profile
        SET location = ?,
            queries = ?,
            exclude_keywords = ?,
            jooble_api_key = ?,
            distance_km = ?
        WHERE id = 1
        """,
        (location, json.dumps(queries), json.dumps(exclude_keywords), jooble_api_key, distance_km),
    )
    conn.commit()
    conn.close()


def save_advanced_filters(
    work_modes: list[str],
    experience_levels: list[str],
    contract_types: list[str],
    schedule_types: list[str],
    salary_min: str,
    protected_categories_mode: str,
    organization_preference: str,
    priority_salary: bool,
    priority_protected: bool,
    priority_remote: bool,
    deduplicate_cross_sites: bool,
    compatibility_enabled: bool,
) -> None:
    conn = get_db()
    conn.execute(
        """
        UPDATE profile
        SET work_modes = ?,
            experience_levels = ?,
            contract_types = ?,
            schedule_types = ?,
            salary_min = ?,
            protected_categories_mode = ?,
            organization_preference = ?,
            priority_salary = ?,
            priority_protected = ?,
            priority_remote = ?,
            deduplicate_cross_sites = ?,
            compatibility_enabled = ?
        WHERE id = 1
        """,
        (
            json.dumps(work_modes),
            json.dumps(experience_levels),
            json.dumps(contract_types),
            json.dumps(schedule_types),
            salary_min,
            protected_categories_mode,
            organization_preference,
            int(priority_salary),
            int(priority_protected),
            int(priority_remote),
            int(deduplicate_cross_sites),
            int(compatibility_enabled),
        ),
    )
    conn.commit()
    conn.close()


def canonical_job_key(job: dict[str, Any]) -> str:
    company = normalize_text(job.get("company"))
    title = normalize_text(job.get("title"))
    title = title.replace("junior", "").replace("senior", "").strip()
    base = f"{company}|{title}" if company or title else str(job.get("link") or "")

    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def has_hard_block(job: dict[str, Any], query: str = "") -> bool:
    text = normalize_text(build_job_text(job))

    if contains_any(text, HARD_BLOCK_TERMS):
        return True

    if "data analyst" in query.lower():
        return contains_any(text, ["brevetti", "patent", "attorney", "meccatronica", "elettronica"])

    return False


def relevance_score(job: dict[str, Any], query: str) -> int:
    text = normalize_text(build_job_text(job))
    title = normalize_text(job.get("title"))
    normalized_query = query.lower().strip()

    if has_hard_block(job, normalized_query):
        return 0

    query_profile = QUERY_PROFILES.get(normalized_query)
    if query_profile is None:
        terms = [word for word in normalize_text(query).split() if len(word) > 3]
        return min(100, sum(18 for term in terms if term in text))

    if contains_any(text, query_profile.get("negative", []) + GLOBAL_NEGATIVE_TERMS):
        return 0

    positive_terms = query_profile["positive"]
    strong_terms = query_profile["strong"]

    positive_hits = sum(1 for term in positive_terms if term in text)
    strong_hits = sum(1 for term in strong_terms if term in text)
    title_hits = sum(1 for term in positive_terms if term in title)

    if positive_hits == 0:
        return 0

    if normalized_query in {"data analyst junior", "web developer junior"}:
        if strong_hits == 0 and title_hits == 0:
            return 0

    if normalized_query in {"comunicazione digitale", "social media manager", "content creator"}:
        if strong_hits == 0 and positive_hits < 2:
            return 0

    return min(100, positive_hits * 12 + strong_hits * 18 + title_hits * 10)


def is_relevant(job: dict[str, Any], query: str, exclude_keywords: list[str]) -> bool:
    text = normalize_text(build_job_text(job))
    title = normalize_text(job.get("title"))

    if any(normalize_text(term) in title or normalize_text(term) in text for term in exclude_keywords):
        return False

    return relevance_score(job, query) >= 24


def is_protected_category(job: dict[str, Any]) -> bool:
    return contains_any(
        normalize_text(build_job_text(job)),
        [
            "legge 68/99",
            "l.68/99",
            "l 68/99",
            "68/99",
            "categorie protette",
            "categoria protetta",
            "invalidita civile",
            "invalidità civile",
            "disabili",
            "disabilita",
            "disabilità",
        ],
    )


def has_salary(job: dict[str, Any]) -> bool:
    return contains_any(
        normalize_text(build_job_text(job)),
        ["€", "eur", "ral", "stipendio", "retribuzione", "salary", "lordi", "netti"],
    )


def is_remote(job: dict[str, Any]) -> bool:
    return contains_any(
        normalize_text(build_job_text(job)),
        ["remoto", "remote", "smart working", "telelavoro", "home working", "da casa"],
    )


def organization_type(job: dict[str, Any]) -> str:
    text = normalize_text(build_job_text(job))

    if contains_any(text, ["comune", "ministero", "università", "universita", "asl", "regione"]):
        return "pa"

    if contains_any(text, ["spa", "s.p.a", "multinazionale", "corporate", "group", "gruppo"]):
        return "large"

    if contains_any(text, ["srl", "s.r.l", "studio", "agenzia", "startup", "pmi"]):
        return "pmi"

    return "unknown"


def matches_salary(job: dict[str, Any], salary_min: str) -> bool:
    if not salary_min:
        return True

    if not has_salary(job):
        return True

    text = normalize_text(build_job_text(job))
    return salary_min in text or f"{int(salary_min) // 1000}k" in text


def passes_filters(job: dict[str, Any], profile: dict[str, Any], query: str) -> bool:
    if not is_within_search_area(profile["location"], str(job.get("location") or ""), profile["distance_km"]):
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


def compatibility_score(job: dict[str, Any], keyword: str, profile: dict[str, Any]) -> tuple[int, list[str]]:
    text = normalize_text(build_job_text(job))
    reasons: list[str] = []
    relevance = relevance_score(job, keyword)
    score = min(46, int(relevance * 0.46))

    if relevance >= 70:
        reasons.append("molto pertinente")
    elif relevance >= 24:
        reasons.append("pertinente")

    matched_terms = [term for term in get_profile_matching_terms() if term in text]
    if matched_terms:
        score += min(24, len(matched_terms) * 4)
        reasons.append("profilo coerente")

    if contains_any(text, ["lm-92", "lm92", "laurea magistrale", "comunicazione d impresa"]):
        score += 10
        reasons.append("LM-92 coerente")

    if contains_any(text, ENTRY_TERMS):
        score += 8
        reasons.append("adatto a profilo junior")

    if contains_any(text, SENIOR_TERMS) and not contains_any(text, ENTRY_TERMS):
        score -= 18
        reasons.append("ruolo più senior")

    if is_protected_category(job):
        score += 15 if profile["priority_protected"] else 8
        reasons.append("categorie protette")

    if is_remote(job):
        score += 12 if profile["priority_remote"] else 6
        reasons.append("remoto")

    if has_salary(job):
        score += 8 if profile["priority_salary"] else 4
        reasons.append("stipendio indicato")

    org_preference = profile["organization_preference"]
    if org_preference != "none" and organization_type(job) == org_preference:
        score += 8
        reasons.append(ORGANIZATION_OPTIONS.get(org_preference, "organizzazione preferita").lower())

    return min(100, max(0, score)), reasons[:6]


def search_jooble(keyword: str, profile: dict[str, Any]) -> list[dict[str, Any]]:
    url = JOOBLE_URL.format(key=profile["jooble_api_key"])
    payload: dict[str, Any] = {
        "keywords": keyword,
        "location": profile["location"],
    }

    if profile["distance_km"].isdigit():
        payload["radius"] = profile["distance_km"]

    try:
        response = requests.post(url, json=payload, timeout=20)
        response.raise_for_status()
    except requests.RequestException:
        return []

    jobs = response.json().get("jobs", [])[:50]
    for job in jobs:
        job["source"] = "Jooble"

    return jobs


def refresh_jobs() -> tuple[int, str | None]:
    profile = get_profile()

    if not profile["location"]:
        return 0, "Imposta prima la tua città in Ricerca."

    if not profile["jooble_api_key"]:
        return 0, "Imposta prima la tua API key Jooble in Ricerca."

    if not profile["queries"]:
        return 0, "Aggiungi almeno una parola chiave di ricerca."

    conn = get_db()
    new_count = 0
    search_location = profile["search_location"]
    collected_jobs: list[tuple[int, list[str], str, str, str, dict[str, Any]]] = []
    seen_canonical_keys: set[str] = set()

    for keyword in profile["queries"]:
        for job in search_jooble(keyword, profile):
            link = job.get("link") or ""
            if not link:
                continue

            canonical_key = canonical_job_key(job)
            external_id = f"{search_location}|{link}"

            if not passes_filters(job, profile, keyword):
                continue

            if profile["deduplicate_cross_sites"] and canonical_key in seen_canonical_keys:
                continue

            seen_canonical_keys.add(canonical_key)

            exists = conn.execute(
                "SELECT id FROM jobs WHERE external_id = ?",
                (external_id,),
            ).fetchone()
            if exists:
                continue

            if profile["deduplicate_cross_sites"]:
                duplicate = conn.execute(
                    "SELECT id FROM jobs WHERE canonical_key = ? AND search_location = ?",
                    (canonical_key, search_location),
                ).fetchone()
                if duplicate:
                    continue

            score, reasons = compatibility_score(job, keyword, profile)
            collected_jobs.append((score, reasons, keyword, canonical_key, external_id, job))

    collected_jobs.sort(key=lambda item: item[0], reverse=True)

    for score, reasons, keyword, canonical_key, external_id, job in collected_jobs:
        conn.execute(
            """
            INSERT INTO jobs (
                external_id,
                canonical_key,
                title,
                company,
                location,
                search_location,
                snippet,
                link,
                updated,
                matched_query,
                compatibility_score,
                priority_reasons,
                status,
                first_seen_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'nuovo', ?)
            """,
            (
                external_id,
                canonical_key,
                job.get("title") or "Senza titolo",
                job.get("company") or "Azienda non specificata",
                job.get("location") or "",
                search_location,
                str(job.get("snippet") or "").replace("&nbsp;", " ").strip(),
                job.get("link") or "",
                job.get("updated") or "",
                keyword,
                score,
                json.dumps(reasons),
                datetime.now().isoformat(timespec="minutes"),
            ),
        )
        new_count += 1

    conn.commit()
    conn.close()

    return new_count, None


def row_to_job(row: sqlite3.Row) -> dict[str, Any]:
    job = dict(row)
    job["priority_reasons"] = load_json_list(job.get("priority_reasons"))
    return job


@app.route("/")
def dashboard():
    profile = get_profile()
    conn = get_db()
    rows = conn.execute(
        """
        SELECT *
        FROM jobs
        WHERE search_location = ?
        ORDER BY compatibility_score DESC, first_seen_at DESC
        LIMIT 150
        """,
        (profile["search_location"],),
    ).fetchall()
    conn.close()

    filtered_jobs = []
    for row in rows:
        job = row_to_job(row)
        if passes_filters(job, profile, job.get("matched_query") or ""):
            filtered_jobs.append(job)

    nuovi = [job for job in filtered_jobs if job["status"] == "nuovo"]
    visti = [job for job in filtered_jobs if job["status"] != "nuovo"]

    return render_template("dashboard.html", nuovi=nuovi, visti=visti, profile=profile)


@app.route("/profilo")
def profilo():
    personal_profile = get_personal_profile()
    return render_template(
        "profilo.html",
        profile=get_profile(),
        profile_data=personal_profile.to_template_context(),
    )


@app.route("/aggiorna", methods=["POST"])
def aggiorna():
    count, error = refresh_jobs()

    if error:
        flash(error, "errore")
    else:
        flash(f"{count} nuovi annunci trovati, filtrati e ordinati per compatibilità.", "successo")

    return redirect(url_for("dashboard"))


@app.route("/segna-visto/<int:job_id>", methods=["POST"])
def segna_visto(job_id: int):
    profile = get_profile()
    conn = get_db()
    conn.execute(
        "UPDATE jobs SET status = 'visto' WHERE id = ? AND search_location = ?",
        (job_id, profile["search_location"]),
    )
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


@app.route("/segna-tutti-visti", methods=["POST"])
def segna_tutti_visti():
    profile = get_profile()
    conn = get_db()
    conn.execute(
        "UPDATE jobs SET status = 'visto' WHERE status = 'nuovo' AND search_location = ?",
        (profile["search_location"],),
    )
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


@app.route("/impostazioni", methods=["GET", "POST"])
def impostazioni():
    if request.method == "POST":
        location = request.form.get("location", "").strip()
        queries = split_comma_values(request.form.get("queries", ""))
        exclude_keywords = split_comma_values(request.form.get("exclude_keywords", ""))
        jooble_api_key = request.form.get("jooble_api_key", "").strip()
        distance_km = request.form.get("distance_km", "").strip()

        if distance_km not in DISTANCE_OPTIONS:
            distance_km = ""

        save_search_settings(location, queries, exclude_keywords, jooble_api_key, distance_km)
        flash("Ricerca salvata. Ora puoi premere Cerca ora dalla Dashboard.", "successo")
        return redirect(url_for("impostazioni"))

    return render_template("impostazioni.html", profile=get_profile())


@app.route("/filtri", methods=["GET", "POST"])
def filtri():
    if request.method == "POST":
        work_modes = [mode for mode in request.form.getlist("work_modes") if mode in WORK_MODE_OPTIONS]
        experience_levels = [
            level for level in request.form.getlist("experience_levels") if level in EXPERIENCE_OPTIONS
        ]
        contract_types = [
            contract for contract in request.form.getlist("contract_types") if contract in CONTRACT_OPTIONS
        ]
        schedule_types = [
            schedule for schedule in request.form.getlist("schedule_types") if schedule in SCHEDULE_OPTIONS
        ]
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
            work_modes=work_modes,
            experience_levels=experience_levels,
            contract_types=contract_types,
            schedule_types=schedule_types,
            salary_min=salary_min,
            protected_categories_mode=protected_mode,
            organization_preference=organization_preference,
            priority_salary="priority_salary" in request.form,
            priority_protected="priority_protected" in request.form,
            priority_remote="priority_remote" in request.form,
            deduplicate_cross_sites="deduplicate_cross_sites" in request.form,
            compatibility_enabled="compatibility_enabled" in request.form,
        )
        flash("Filtri e priorità salvati. Verranno applicati alla prossima ricerca.", "successo")
        return redirect(url_for("filtri"))

    return render_template("filtri.html", profile=get_profile())


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
