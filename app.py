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

# Parole chiave di partenza, ricavate dal profilo di Andrea (comunicazione,
# giornalismo, social media, più le competenze digitali/tecniche da CV).
# Si modificano liberamente dalla pagina Impostazioni.
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


# ----------------------------------------------------------------------
# Database — un solo profilo, nessun utente da gestire
# ----------------------------------------------------------------------

def normalize_location(location: str) -> str:
    """Rende confrontabili le città salvate, evitando differenze maiuscole/spazi."""
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
            experience_levels TEXT DEFAULT '[]'
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
    ensure_column(conn, "jobs", "search_location", "TEXT")
    row = conn.execute("SELECT id FROM profile WHERE id = 1").fetchone()
    if row is None:
        conn.execute(
            """INSERT INTO profile
               (id, location, queries, exclude_keywords, distance_km, work_modes, experience_levels)
               VALUES (1, ?, ?, ?, '', '[]', '[]')""",
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
    work_modes = load_json_list(row["work_modes"])
    experience_levels = load_json_list(row["experience_levels"])
    return {
        "location": row["location"],
        "search_location": normalize_location(row["location"]),
        "queries": load_json_list(row["queries"]),
        "exclude_keywords": load_json_list(row["exclude_keywords"]),
        "jooble_api_key": row["jooble_api_key"],
        "distance_km": row["distance_km"] or "",
        "work_modes": work_modes,
        "experience_levels": experience_levels,
        "work_mode_options": WORK_MODE_OPTIONS,
        "experience_options": EXPERIENCE_OPTIONS,
    }


def save_profile(location, queries, exclude_keywords, jooble_api_key, distance_km, work_modes, experience_levels):
    conn = get_db()
    conn.execute(
        """UPDATE profile
           SET location=?, queries=?, exclude_keywords=?, jooble_api_key=?,
               distance_km=?, work_modes=?, experience_levels=?
           WHERE id=1""",
        (
            location,
            json.dumps(queries),
            json.dumps(exclude_keywords),
            jooble_api_key,
            distance_km,
            json.dumps(work_modes),
            json.dumps(experience_levels),
        ),
    )
    conn.commit()
    conn.close()


# ----------------------------------------------------------------------
# Ricerca annunci
# ----------------------------------------------------------------------

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


def passes_filters(job: dict, profile: dict) -> bool:
    return (
        matches_work_modes(job, profile["work_modes"])
        and matches_experience_levels(job, profile["experience_levels"])
    )


def search_jooble(keyword: str, profile: dict) -> list:
    url = JOOBLE_URL.format(key=profile["jooble_api_key"])
    payload = {"keywords": keyword, "location": profile["location"]}

    # Jooble può usare il raggio se supportato dalla chiave/API; in caso contrario
    # la richiesta continua comunque a funzionare con città e parole chiave.
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
        return 0, "Imposta prima la tua città in Impostazioni."
    if not profile["jooble_api_key"]:
        return 0, "Imposta prima la tua API key Jooble in Impostazioni."
    if not profile["queries"]:
        return 0, "Aggiungi almeno una parola chiave di ricerca in Impostazioni."

    conn = get_db()
    new_count = 0
    search_location = profile["search_location"]

    for keyword in profile["queries"]:
        results = search_jooble(keyword, profile)
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


# ----------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------

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
        work_modes = [mode for mode in request.form.getlist("work_modes") if mode in WORK_MODE_OPTIONS]
        experience_levels = [level for level in request.form.getlist("experience_levels") if level in EXPERIENCE_OPTIONS]

        save_profile(location, queries, exclude, jooble_api_key, distance_km, work_modes, experience_levels)
        flash("Impostazioni salvate. La dashboard mostrerà solo gli annunci compatibili con area e filtri.", "successo")
        return redirect(url_for("impostazioni"))

    return render_template("impostazioni.html", profile=get_profile())


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
