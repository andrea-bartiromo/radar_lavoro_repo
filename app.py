"""
Radar Lavoro — il tuo aggregatore di offerte personale

Nessun account, nessun login: è pensato per un solo utente (te), in esecuzione
sul tuo computer. Cerca offerte di lavoro nel territorio che scegli, basandosi
su parole chiave derivate dal tuo profilo/CV, e ti mostra solo le novità.

Avvio: python app.py
Poi apri http://127.0.0.1:5000
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

import requests
from flask import Flask, render_template, request, redirect, url_for, flash

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
    "elettricista", "infermiere", "OSS", "badante",
    "animatore", "animatrice", "animazione", "fotomodell", "ballerin",
    "casting", "hostess", "beauty consultant", "consulente di bellezza",
    "informatore scientifico", "informatore medico", "sales assistant",
    "addetto vendit", "addetta vendit", "store manager", "agente di commercio",
    "venditore", "rappresentante", "ragazze immagine", "operatrice", "reception",
    "modell", "district manager", "area manager contratti", "beauty",
]

DISTANCE_OPTIONS = {
    "": "Solo città / area indicata",
    "10": "Entro 10 km",
    "25": "Entro 25 km",
    "50": "Entro 50 km",
    "100": "Entro 100 km",
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

RELEVANCE_TERMS = {
    "comunicazione digitale": ["comunicazion", "digital", "content", "media"],
    "social media manager": ["social", "media"],
    "content creator": ["content", "creator", "creatore", "creazione contenut"],
    "copywriter": ["copywriter", "copy", "redattor", "redazion"],
    "giornalista redattore": ["giornalist", "redattor", "redazion"],
    "ufficio stampa": ["stampa", "comunicazion", "press"],
    "data analyst junior": ["data", "analyst", "analista", "dati"],
    "web developer junior": ["developer", "svilupp", "programmator", "web"],
}
PAROLE_TROPPO_GENERICHE = {"junior", "senior", "manager", "specialist", "responsabile"}

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
            protected_categories_mode TEXT DEFAULT 'off'
        );

        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            external_id TEXT UNIQUE,
            title TEXT,
            company TEXT,
            location TEXT,
            search_location TEXT,
            snippet TEXT,
            link TEXT,
            updated TEXT,
            matched_query TEXT,
            status TEXT DEFAULT 'nuovo',
            first_seen_at TEXT
        );
        """
    )
    ensure_column(conn, "profile", "distance_km", "TEXT DEFAULT ''")
    ensure_column(conn, "profile", "work_modes", "TEXT DEFAULT '[]'")
    ensure_column(conn, "profile", "experience_levels", "TEXT DEFAULT '[]'")
    ensure_column(conn, "profile", "contract_types", "TEXT DEFAULT '[]'")
    ensure_column(conn, "profile", "schedule_types", "TEXT DEFAULT '[]'")
    ensure_column(conn, "profile", "salary_min", "TEXT DEFAULT ''")
    ensure_column(conn, "profile", "protected_categories_mode", "TEXT DEFAULT 'off'")
    ensure_column(conn, "jobs", "search_location", "TEXT")

    row = conn.execute("SELECT id FROM profile WHERE id = 1").fetchone()
    if row is None:
        conn.execute(
            """INSERT INTO profile
               (id, location, queries, exclude_keywords, distance_km, work_modes,
                experience_levels, contract_types, schedule_types, salary_min, protected_categories_mode)
               VALUES (1, ?, ?, ?, '', '[]', '[]', '[]', '[]', '', 'off')""",
            ("", json.dumps(DEFAULT_QUERIES), json.dumps(DEFAULT_EXCLUDE)),
        )
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
        "distance_options": DISTANCE_OPTIONS,
        "work_mode_options": WORK_MODE_OPTIONS,
        "experience_options": EXPERIENCE_OPTIONS,
        "contract_options": CONTRACT_OPTIONS,
        "schedule_options": SCHEDULE_OPTIONS,
        "salary_options": SALARY_OPTIONS,
        "protected_options": PROTECTED_OPTIONS,
    }


def save_search_settings(location, queries, exclude_keywords, jooble_api_key, distance_km):
    conn = get_db()
    conn.execute(
        """UPDATE profile
           SET location=?, queries=?, exclude_keywords=?, jooble_api_key=?, distance_km=?
           WHERE id=1""",
        (location, json.dumps(queries), json.dumps(exclude_keywords), jooble_api_key, distance_km),
    )
    conn.commit()
    conn.close()


def save_advanced_filters(work_modes, experience_levels, contract_types, schedule_types, salary_min, protected_categories_mode):
    conn = get_db()
    conn.execute(
        """UPDATE profile
           SET work_modes=?, experience_levels=?, contract_types=?, schedule_types=?,
               salary_min=?, protected_categories_mode=?
           WHERE id=1""",
        (
            json.dumps(work_modes),
            json.dumps(experience_levels),
            json.dumps(contract_types),
            json.dumps(schedule_types),
            salary_min,
            protected_categories_mode,
        ),
    )
    conn.commit()
    conn.close()


def testo_annuncio(job: dict) -> str:
    return " ".join([
        job.get("title") or "",
        job.get("company") or "",
        job.get("location") or "",
        job.get("snippet") or "",
    ]).lower()


def contains_any(text: str, terms: list) -> bool:
    return any(term in text for term in terms)


def is_relevant(title: str, exclude_keywords: list) -> bool:
    title_lower = (title or "").lower()
    return not any(bad.lower() in title_lower for bad in exclude_keywords)


def titolo_e_pertinente(title: str, query: str) -> bool:
    title_lower = (title or "").lower()
    query_lower = query.lower()
    termini = RELEVANCE_TERMS.get(query_lower)
    if termini is None:
        termini = [
            parola for parola in query_lower.split()
            if len(parola) > 3 and parola not in PAROLE_TROPPO_GENERICHE
        ]
        if not termini:
            return True
    return any(t in title_lower for t in termini)


def is_protected_category(job: dict) -> bool:
    text = testo_annuncio(job)
    protected_terms = [
        "legge 68/99", "l.68/99", "l 68/99", "68/99", "categorie protette",
        "categoria protetta", "art. 1", "art 1", "invalidità civile", "invalidita civile",
        "disabili", "disabilità", "disabilita", "protected categories", "disability",
    ]
    return contains_any(text, protected_terms)


def matches_work_modes(job: dict, selected_modes: list) -> bool:
    if not selected_modes:
        return True
    text = testo_annuncio(job)
    mode_terms = {
        "remote": ["remoto", "remote", "smart working", "telelavoro", "home working", "da casa"],
        "hybrid": ["ibrido", "ibrida", "hybrid", "misto", "mista", "parzialmente da remoto"],
        "onsite": ["in sede", "in presenza", "on site", "onsite", "ufficio", "sede di lavoro"],
    }
    return any(contains_any(text, mode_terms.get(mode, [])) for mode in selected_modes)


def matches_experience_levels(job: dict, selected_levels: list) -> bool:
    if not selected_levels:
        return True
    text = testo_annuncio(job)
    level_terms = {
        "internship": ["stage", "tirocinio", "internship", "stagista", "curriculare", "extracurriculare"],
        "entry": ["junior", "entry level", "neolaureato", "neolaureata", "apprendistato", "prima esperienza"],
        "mid": ["middle", "intermedio", "2 anni", "3 anni", "esperienza pregressa", "specialist"],
        "senior": ["senior", "lead", "responsabile", "coordinator", "coordinatore", "5 anni"],
    }
    return any(contains_any(text, level_terms.get(level, [])) for level in selected_levels)


def matches_contract_types(job: dict, selected_contracts: list) -> bool:
    if not selected_contracts:
        return True
    text = testo_annuncio(job)
    contract_terms = {
        "permanent": ["tempo indeterminato", "indeterminato", "permanent"],
        "fixed_term": ["tempo determinato", "determinato", "fixed term"],
        "apprenticeship": ["apprendistato", "apprenticeship"],
        "internship": ["stage", "tirocinio", "internship"],
        "freelance": ["freelance", "collaborazione", "partita iva", "p. iva", "p iva", "consulenza"],
    }
    return any(contains_any(text, contract_terms.get(contract, [])) for contract in selected_contracts)


def matches_schedule_types(job: dict, selected_schedules: list) -> bool:
    if not selected_schedules:
        return True
    text = testo_annuncio(job)
    schedule_terms = {
        "full_time": ["full time", "full-time", "tempo pieno"],
        "part_time": ["part time", "part-time", "tempo parziale"],
        "flexible": ["flessibile", "orario flessibile", "smart working", "da remoto"],
    }
    return any(contains_any(text, schedule_terms.get(schedule, [])) for schedule in selected_schedules)


def matches_salary(job: dict, salary_min: str) -> bool:
    # La maggior parte degli annunci Jooble non espone una RAL strutturata.
    # Per evitare falsi negativi, il filtro stipendio viene applicato solo quando
    # il testo contiene informazioni economiche riconoscibili.
    if not salary_min:
        return True
    text = testo_annuncio(job)
    if "€" not in text and "ral" not in text and "stipendio" not in text and "retribuzione" not in text:
        return True
    return salary_min in text or f"{int(salary_min) // 1000}k" in text


def passes_filters(job: dict, profile: dict) -> bool:
    if profile["protected_categories_mode"] == "only" and not is_protected_category(job):
        return False
    return (
        matches_work_modes(job, profile["work_modes"])
        and matches_experience_levels(job, profile["experience_levels"])
        and matches_contract_types(job, profile["contract_types"])
        and matches_schedule_types(job, profile["schedule_types"])
        and matches_salary(job, profile["salary_min"])
    )


def sort_jobs_for_priority(jobs: list, profile: dict) -> list:
    if profile["protected_categories_mode"] != "priority":
        return jobs
    return sorted(jobs, key=lambda job: 0 if is_protected_category(job) else 1)


def search_jooble(keyword: str, profile: dict) -> list:
    url = JOOBLE_URL.format(key=profile["jooble_api_key"])
    payload = {"keywords": keyword, "location": profile["location"]}
    if profile["distance_km"]:
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
        return 0, "Imposta prima la tua città in Ricerca."
    if not profile["jooble_api_key"]:
        return 0, "Imposta prima la tua API key Jooble in Ricerca."
    if not profile["queries"]:
        return 0, "Aggiungi almeno una parola chiave di ricerca."

    conn = get_db()
    new_count = 0
    search_location = profile["search_location"]

    for keyword in profile["queries"]:
        results = sort_jobs_for_priority(search_jooble(keyword, profile), profile)
        for job in results:
            link = job.get("link") or ""
            title = job.get("title") or "Senza titolo"
            external_id = f"{search_location}|{link}"

            if not link or not is_relevant(title, profile["exclude_keywords"]):
                continue
            if not titolo_e_pertinente(title, keyword):
                continue
            if not passes_filters(job, profile):
                continue

            exists = conn.execute("SELECT id FROM jobs WHERE external_id = ?", (external_id,)).fetchone()
            if exists:
                continue

            conn.execute(
                """INSERT INTO jobs (external_id, title, company, location, search_location, snippet, link,
                   updated, matched_query, status, first_seen_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'nuovo', ?)""",
                (
                    external_id,
                    title,
                    job.get("company", "Azienda non specificata"),
                    job.get("location", ""),
                    search_location,
                    (job.get("snippet") or "").replace("&nbsp;", " ").strip(),
                    link,
                    job.get("updated", ""),
                    keyword,
                    datetime.now().isoformat(timespec="minutes"),
                ),
            )
            new_count += 1

    conn.commit()
    conn.close()
    return new_count, None


@app.route("/")
def dashboard():
    profile = get_profile()
    conn = get_db()
    jobs = conn.execute(
        """SELECT * FROM jobs
           WHERE search_location = ?
           ORDER BY first_seen_at DESC
           LIMIT 150""",
        (profile["search_location"],),
    ).fetchall()
    conn.close()
    nuovi = [j for j in jobs if j["status"] == "nuovo"]
    visti = [j for j in jobs if j["status"] != "nuovo"]
    return render_template("dashboard.html", nuovi=nuovi, visti=visti, profile=profile)


@app.route("/aggiorna", methods=["POST"])
def aggiorna():
    count, error = refresh_jobs()
    if error:
        flash(error, "errore")
    else:
        flash(f"{count} nuovi annunci trovati per questa area e questi filtri.", "successo")
    return redirect(url_for("dashboard"))


@app.route("/segna-visto/<int:job_id>", methods=["POST"])
def segna_visto(job_id):
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
        if salary_min not in SALARY_OPTIONS:
            salary_min = ""
        if protected_mode not in PROTECTED_OPTIONS:
            protected_mode = "off"
        save_advanced_filters(work_modes, experience_levels, contract_types, schedule_types, salary_min, protected_mode)
        flash("Filtri avanzati salvati. Verranno applicati alla prossima ricerca.", "successo")
        return redirect(url_for("filtri"))
    return render_template("filtri.html", profile=get_profile())


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
