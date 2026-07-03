"""Gestione candidature per Radar Lavoro.

Questo modulo contiene la logica del primo CRM personale:
- stati candidatura;
- normalizzazione stato;
- preparazione dati per la dashboard;
- aggiornamento candidatura su database SQLite.
"""

from datetime import datetime
from typing import Mapping


APPLICATION_STATUS_OPTIONS = {
    "nuovo": "Nuovo",
    "visto": "Visto",
    "salvato": "Salvato",
    "cv_preparato": "CV preparato",
    "candidatura_inviata": "Candidatura inviata",
    "colloquio": "Colloquio",
    "scartato": "Scartato",
    "assunto": "Assunto",
}

ACTIVE_APPLICATION_STATUSES = {
    "salvato",
    "cv_preparato",
    "candidatura_inviata",
    "colloquio",
}

FINAL_APPLICATION_STATUSES = {
    "scartato",
    "assunto",
}


def normalize_application_status(value: str | None, fallback: str = "visto") -> str:
    """Restituisce uno stato candidatura valido."""
    value = (value or "").strip()
    if value in APPLICATION_STATUS_OPTIONS:
        return value
    return fallback if fallback in APPLICATION_STATUS_OPTIONS else "visto"


def application_status_label(value: str | None) -> str:
    """Etichetta leggibile per la UI."""
    status = normalize_application_status(value, fallback="visto")
    return APPLICATION_STATUS_OPTIONS[status]


def enrich_job_for_application(job: dict) -> dict:
    """Aggiunge campi derivati utili alla dashboard."""
    status = normalize_application_status(
        job.get("application_status") or job.get("status"),
        fallback="nuovo",
    )
    job["application_status"] = status
    job["application_status_label"] = application_status_label(status)
    job["is_active_application"] = status in ACTIVE_APPLICATION_STATUSES
    job["is_final_application"] = status in FINAL_APPLICATION_STATUSES
    return job


def split_jobs_by_application_status(jobs: list[dict]) -> tuple[list[dict], list[dict], dict]:
    """Divide annunci nuovi e candidature/offerte seguite, calcolando statistiche base."""
    enriched = [enrich_job_for_application(job) for job in jobs]
    nuovi = [job for job in enriched if job["application_status"] == "nuovo"]
    seguiti = [job for job in enriched if job["application_status"] != "nuovo"]
    stats = {
        "nuovi": len(nuovi),
        "salvati": len([job for job in enriched if job["application_status"] == "salvato"]),
        "cv_preparati": len([job for job in enriched if job["application_status"] == "cv_preparato"]),
        "candidate": len([job for job in enriched if job["application_status"] == "candidatura_inviata"]),
        "colloqui": len([job for job in enriched if job["application_status"] == "colloquio"]),
        "scartati": len([job for job in enriched if job["application_status"] == "scartato"]),
        "assunzioni": len([job for job in enriched if job["application_status"] == "assunto"]),
    }
    return nuovi, seguiti, stats


def update_application(conn, job_id: int, search_location: str, form: Mapping[str, str]) -> None:
    """Aggiorna stato candidatura e note personali per un annuncio."""
    new_status = normalize_application_status(form.get("application_status"), fallback="visto")
    notes = (form.get("personal_notes") or "").strip()
    now = datetime.now().isoformat(timespec="minutes")

    row = conn.execute(
        "SELECT applied_at FROM jobs WHERE id = ? AND search_location = ?",
        (job_id, search_location),
    ).fetchone()
    if row is None:
        return

    current_applied_at = row["applied_at"] if "applied_at" in row.keys() else ""
    applied_at = current_applied_at or (now if new_status == "candidatura_inviata" else "")

    conn.execute(
        """
        UPDATE jobs
           SET application_status = ?,
               personal_notes = ?,
               applied_at = ?,
               last_status_at = ?,
               status = CASE WHEN status = 'nuovo' THEN 'visto' ELSE status END
         WHERE id = ? AND search_location = ?
        """,
        (new_status, notes, applied_at, now, job_id, search_location),
    )
