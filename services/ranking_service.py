"""Ranking e compatibilità degli annunci.

Questo modulo trasforma il risultato del matching in un punteggio ordinabile e
in una lista di motivazioni leggibili in dashboard.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from services.matching_service import ENTRY_TERMS, SENIOR_TERMS, MatchResult
from services.text_service import build_job_text, contains_any, normalize_text


PROTECTED_TERMS = [
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
]

REMOTE_TERMS = [
    "remoto",
    "remote",
    "smart working",
    "telelavoro",
    "home working",
    "da casa",
]

SALARY_TERMS = [
    "€",
    "eur",
    "ral",
    "stipendio",
    "retribuzione",
    "salary",
    "lordi",
    "netti",
]

PUBLIC_ADMINISTRATION_TERMS = [
    "comune",
    "ministero",
    "università",
    "universita",
    "asl",
    "regione",
    "provincia",
    "ente pubblico",
    "pubblica amministrazione",
]

LARGE_COMPANY_TERMS = [
    "spa",
    "s.p.a",
    "multinazionale",
    "corporate",
    "group",
    "gruppo",
    "holding",
    "enterprise",
]

PMI_TERMS = [
    "srl",
    "s.r.l",
    "studio",
    "agenzia",
    "startup",
    "start up",
    "pmi",
]


@dataclass(slots=True)
class RankingResult:
    """Risultato finale del ranking di un annuncio."""

    score: int
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def has_salary(job: dict[str, Any]) -> bool:
    """Indica se l'annuncio mostra una retribuzione o una RAL."""

    return contains_any(normalize_text(build_job_text(job)), SALARY_TERMS)


def is_remote(job: dict[str, Any]) -> bool:
    """Indica se l'annuncio contiene segnali di lavoro remoto."""

    return contains_any(normalize_text(build_job_text(job)), REMOTE_TERMS)


def is_protected_category(job: dict[str, Any]) -> bool:
    """Indica se l'annuncio cita categorie protette o L.68/99."""

    return contains_any(normalize_text(build_job_text(job)), PROTECTED_TERMS)


def organization_type(job: dict[str, Any]) -> str:
    """Stima il tipo di organizzazione dell'annuncio."""

    text = normalize_text(build_job_text(job))

    if contains_any(text, PUBLIC_ADMINISTRATION_TERMS):
        return "pa"

    if contains_any(text, LARGE_COMPANY_TERMS):
        return "large"

    if contains_any(text, PMI_TERMS):
        return "pmi"

    return "unknown"


def rank_job(job: dict[str, Any], match: MatchResult, profile: dict[str, Any]) -> RankingResult:
    """Calcola punteggio e motivazioni finali per la dashboard."""

    text = normalize_text(build_job_text(job))
    reasons = list(match.reasons)
    warnings: list[str] = []

    score = min(46, int(match.relevance_score * 0.46))

    if match.profile_matches:
        score += min(24, len(match.profile_matches) * 4)

    if contains_any(text, ["lm-92", "lm92", "laurea magistrale", "comunicazione d impresa"]):
        score += 10
        reasons.append("LM-92 coerente")

    if contains_any(text, ENTRY_TERMS):
        score += 8
        reasons.append("adatto a profilo junior")

    if contains_any(text, SENIOR_TERMS) and not contains_any(text, ENTRY_TERMS):
        score -= 18
        warnings.append("ruolo più senior")

    if is_protected_category(job):
        score += 15 if profile.get("priority_protected") else 8
        reasons.append("categorie protette")

    if is_remote(job):
        score += 12 if profile.get("priority_remote") else 6
        reasons.append("remoto")

    if has_salary(job):
        score += 8 if profile.get("priority_salary") else 4
        reasons.append("stipendio indicato")

    preferred_organization = profile.get("organization_preference")
    if preferred_organization and preferred_organization != "none":
        if organization_type(job) == preferred_organization:
            score += 8
            reasons.append("organizzazione preferita")

    return RankingResult(
        score=min(100, max(0, score)),
        reasons=_deduplicate_labels(reasons),
        warnings=_deduplicate_labels(warnings),
    )


def _deduplicate_labels(labels: list[str]) -> list[str]:
    """Rimuove motivazioni duplicate mantenendo l'ordine originale."""

    unique_labels: list[str] = []
    seen: set[str] = set()

    for label in labels:
        if label in seen:
            continue

        seen.add(label)
        unique_labels.append(label)

    return unique_labels[:6]
