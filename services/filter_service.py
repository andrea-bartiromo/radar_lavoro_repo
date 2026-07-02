"""Filtri avanzati prudenziali per gli annunci.

Principio importante: se un annuncio non dichiara un'informazione, non deve
essere escluso automaticamente. Molti portali non indicano sempre modalità,
contratto, esperienza o orario; per questo i filtri devono essere permissivi
quando il dato è assente.
"""

from __future__ import annotations

from services.text_service import build_job_text, contains_any


WORK_MODE_TERMS = {
    "remote": ["remoto", "remote", "smart working", "telelavoro", "home working", "da casa"],
    "hybrid": ["ibrido", "ibrida", "hybrid", "misto", "mista", "parzialmente da remoto"],
    "onsite": ["in sede", "in presenza", "on site", "onsite", "ufficio", "sede di lavoro"],
}

EXPERIENCE_TERMS = {
    "internship": ["stage", "tirocinio", "internship", "stagista", "curriculare", "extracurriculare"],
    "entry": ["junior", "entry level", "neolaureato", "neolaureata", "apprendistato", "prima esperienza"],
    "mid": ["middle", "intermedio", "2 anni", "3 anni", "esperienza pregressa", "specialist"],
    "senior": ["senior", "lead", "responsabile", "head of", "coordinator", "coordinatore", "manager", "team lead", "5 anni"],
}

CONTRACT_TERMS = {
    "permanent": ["tempo indeterminato", "indeterminato", "permanent"],
    "fixed_term": ["tempo determinato", "determinato", "fixed term"],
    "apprenticeship": ["apprendistato", "apprenticeship"],
    "internship": ["stage", "tirocinio", "internship"],
    "freelance": ["freelance", "collaborazione", "partita iva", "p. iva", "p iva", "consulenza"],
}

SCHEDULE_TERMS = {
    "full_time": ["full time", "full-time", "tempo pieno"],
    "part_time": ["part time", "part-time", "tempo parziale"],
    "flexible": ["flessibile", "orario flessibile", "smart working", "da remoto"],
}


def has_declared_value(text: str, vocabulary: dict[str, list[str]]) -> bool:
    """Indica se l'annuncio dichiara almeno un valore del vocabolario."""

    return any(contains_any(text, terms) for terms in vocabulary.values())


def matches_selected_values(text: str, selected: list[str], vocabulary: dict[str, list[str]]) -> bool:
    """Applica un filtro solo se il dato è dichiarato nell'annuncio.

    Se l'utente non seleziona nulla, il filtro è spento.
    Se seleziona tutte le opzioni, equivale a non filtrare.
    Se l'annuncio non dichiara il dato, viene mantenuto.
    """

    if not selected:
        return True

    if set(selected) >= set(vocabulary):
        return True

    if not has_declared_value(text, vocabulary):
        return True

    return any(contains_any(text, vocabulary.get(value, [])) for value in selected)


def matches_work_modes(job: dict, selected_modes: list[str]) -> bool:
    """Filtra per modalità di lavoro senza scartare gli annunci incompleti."""

    return matches_selected_values(build_job_text(job), selected_modes, WORK_MODE_TERMS)


def matches_experience_levels(job: dict, selected_levels: list[str]) -> bool:
    """Filtra per seniority senza scartare gli annunci incompleti."""

    return matches_selected_values(build_job_text(job), selected_levels, EXPERIENCE_TERMS)


def matches_contract_types(job: dict, selected_contracts: list[str]) -> bool:
    """Filtra per contratto senza scartare gli annunci incompleti."""

    return matches_selected_values(build_job_text(job), selected_contracts, CONTRACT_TERMS)


def matches_schedule_types(job: dict, selected_schedules: list[str]) -> bool:
    """Filtra per orario senza scartare gli annunci incompleti."""

    return matches_selected_values(build_job_text(job), selected_schedules, SCHEDULE_TERMS)
