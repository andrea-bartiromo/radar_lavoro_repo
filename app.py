"""
Radar Lavoro — il tuo aggregatore di offerte personale

Nessun account, nessun login: è pensato per un solo utente (te), in esecuzione
sul tuo computer. Cerca offerte di lavoro nel territorio che scegli, basandosi
su parole chiave derivate dal tuo profilo/CV, e ti mostra solo le novità.

Avvio: python app.py
Poi apri http://127.0.0.1:5000
"""

import json
import os
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

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            location TEXT DEFAULT '',
            queries TEXT DEFAULT '[]',
            exclude_keywords TEXT DEFAULT '[]',
            jooble_api_key TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            external_id TEXT UNIQUE,
            title TEXT,
            company TEXT,
            location TEXT,
            snippet TEXT,
            link TEXT,
            updated TEXT,
            matched_query TEXT,
            status TEXT DEFAULT 'nuovo',
            first_seen_at TEXT
        );
        """
    )
    row = conn.execute("SELECT id FROM profile WHERE id = 1").fetchone()
    if row is None:
        conn.execute(
            "INSERT INTO profile (id, location, queries, exclude_keywords) VALUES (1, ?, ?, ?)",
            ("", json.dumps(DEFAULT_QUERIES), json.dumps(DEFAULT_EXCLUDE)),
        )
    conn.commit()
    conn.close()


def get_profile():
    conn = get_db()
    row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    conn.close()
    return {
        "location": row["location"],
        "queries": json.loads(row["queries"]),
        "exclude_keywords": json.loads(row["exclude_keywords"]),
        "jooble_api_key": row["jooble_api_key"],
    }


def save_profile(location, queries, exclude_keywords, jooble_api_key):
    conn = get_db()
    conn.execute(
        "UPDATE profile SET location=?, queries=?, exclude_keywords=?, jooble_api_key=? WHERE id=1",
        (location, json.dumps(queries), json.dumps(exclude_keywords), jooble_api_key),
    )
    conn.commit()
    conn.close()


# ----------------------------------------------------------------------
# Ricerca annunci
# ----------------------------------------------------------------------

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


def search_jooble(keyword: str, location: str, api_key: str) -> list:
    url = JOOBLE_URL.format(key=api_key)
    try:
        resp = requests.post(url, json={"keywords": keyword, "location": location}, timeout=20)
        resp.raise_for_status()
        return resp.json().get("jobs", [])[:20]
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

    for keyword in profile["queries"]:
        results = search_jooble(keyword, profile["location"], profile["jooble_api_key"])
        for job in results:
            link = job.get("link") or ""
            title = job.get("title") or "Senza titolo"
            if not link or not is_relevant(title, profile["exclude_keywords"]):
                continue
            if not titolo_e_pertinente(title, keyword):
                continue
            exists = conn.execute("SELECT id FROM jobs WHERE external_id = ?", (link,)).fetchone()
            if exists:
                continue
            conn.execute(
                """INSERT INTO jobs (external_id, title, company, location, snippet, link,
                   updated, matched_query, status, first_seen_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'nuovo', ?)""",
                (
                    link, title,
                    job.get("company", "Azienda non specificata"),
                    job.get("location", ""),
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
    conn = get_db()
    jobs = conn.execute("SELECT * FROM jobs ORDER BY first_seen_at DESC LIMIT 150").fetchall()
    conn.close()
    nuovi = [j for j in jobs if j["status"] == "nuovo"]
    visti = [j for j in jobs if j["status"] != "nuovo"]
    return render_template("dashboard.html", nuovi=nuovi, visti=visti, profile=get_profile())


@app.route("/aggiorna", methods=["POST"])
def aggiorna():
    count, error = refresh_jobs()
    if error:
        flash(error, "errore")
    else:
        flash(f"{count} nuovi annunci trovati.", "successo")
    return redirect(url_for("dashboard"))


@app.route("/segna-visto/<int:job_id>", methods=["POST"])
def segna_visto(job_id):
    conn = get_db()
    conn.execute("UPDATE jobs SET status = 'visto' WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))


@app.route("/segna-tutti-visti", methods=["POST"])
def segna_tutti_visti():
    conn = get_db()
    conn.execute("UPDATE jobs SET status = 'visto' WHERE status = 'nuovo'")
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

        save_profile(location, queries, exclude, jooble_api_key)
        flash("Impostazioni salvate.", "successo")
        return redirect(url_for("impostazioni"))

    return render_template("impostazioni.html", profile=get_profile())


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
