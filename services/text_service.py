"""Utility testuali condivise da filtri, ranking e deduplica."""

from __future__ import annotations

import re
from collections.abc import Mapping


JobLike = Mapping[str, object]


def normalize_text(value: object) -> str:
    """Normalizza testo HTML/libero rendendolo confrontabile.

    La funzione rimuove tag HTML, caratteri non utili e spazi doppi. È pensata
    per confronti robusti su titoli, descrizioni e località degli annunci.
    """

    text = str(value or "").lower()
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[^a-z0-9àèéìòù.+#/-]+", " ", text)
    return " ".join(text.split())


def build_job_text(job: JobLike) -> str:
    """Unisce i campi principali dell'annuncio in una sola stringa."""

    fields = [
        job.get("title"),
        job.get("company"),
        job.get("location"),
        job.get("snippet"),
    ]

    return " ".join(str(field or "") for field in fields).lower()


def contains_any(text: str, terms: list[str]) -> bool:
    """Restituisce True se almeno uno dei termini compare nel testo."""

    return any(term in text for term in terms)


def count_matches(text: str, terms: list[str]) -> int:
    """Conta quanti termini della lista sono presenti nel testo."""

    return sum(1 for term in terms if term in text)


def split_comma_values(value: str) -> list[str]:
    """Converte una stringa separata da virgole in una lista pulita."""

    return [item.strip() for item in value.split(",") if item.strip()]
