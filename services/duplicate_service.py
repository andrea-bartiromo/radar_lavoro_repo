"""Deduplicazione degli annunci di lavoro.

Questo servizio costruisce chiavi stabili per riconoscere annunci uguali o quasi
uguali anche quando arrivano da fonti diverse.
"""

from __future__ import annotations

import hashlib
from typing import Any

from services.text_service import normalize_text


NOISE_WORDS = [
    "junior",
    "senior",
    "middle",
    "full time",
    "part time",
    "orario flessibile",
    "smart working",
    "remoto",
    "ibrido",
]


def clean_title(title: object) -> str:
    """Pulisce il titolo rimuovendo parole poco utili per la deduplica."""

    cleaned = normalize_text(title)

    for word in NOISE_WORDS:
        cleaned = cleaned.replace(word, " ")

    return " ".join(cleaned.split())


def canonical_job_key(job: dict[str, Any]) -> str:
    """Crea una chiave stabile azienda + titolo per riconoscere duplicati."""

    company = normalize_text(job.get("company"))
    title = clean_title(job.get("title"))

    if not company and not title:
        base = str(job.get("link") or "")
    else:
        base = f"{company}|{title}"

    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def remove_duplicates(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rimuove duplicati all'interno di una lista di annunci."""

    unique_jobs: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    for job in jobs:
        key = canonical_job_key(job)

        if key in seen_keys:
            continue

        seen_keys.add(key)
        unique_jobs.append(job)

    return unique_jobs
