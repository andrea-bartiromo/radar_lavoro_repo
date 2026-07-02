"""Stati del ciclo di vita di un annuncio.

Questo modulo definisce gli stati che useremo per trasformare Radar Lavoro in
un archivio personale delle opportunità e delle candidature.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class JobStatus:
    """Descrive uno stato assegnabile a un annuncio."""

    value: str
    label: str
    icon: str
    description: str


NEW = JobStatus(
    value="nuovo",
    label="Nuovo",
    icon="🆕",
    description="Annuncio appena trovato e non ancora valutato.",
)

SEEN = JobStatus(
    value="visto",
    label="Già visto",
    icon="👀",
    description="Annuncio consultato ma non ancora classificato.",
)

FAVORITE = JobStatus(
    value="preferito",
    label="Preferito",
    icon="⭐",
    description="Annuncio interessante da tenere in evidenza.",
)

APPLIED = JobStatus(
    value="candidato",
    label="Candidatura inviata",
    icon="📤",
    description="Candidatura già inviata.",
)

INTERVIEW = JobStatus(
    value="colloquio",
    label="Colloquio",
    icon="📞",
    description="Annuncio collegato a un colloquio o contatto attivo.",
)

REJECTED = JobStatus(
    value="scartato",
    label="Scartato",
    icon="❌",
    description="Annuncio non più interessante o non adatto.",
)

HIRED = JobStatus(
    value="assunto",
    label="Assunto",
    icon="🎉",
    description="Opportunità conclusa positivamente.",
)

JOB_STATUSES = [
    NEW,
    SEEN,
    FAVORITE,
    APPLIED,
    INTERVIEW,
    REJECTED,
    HIRED,
]

JOB_STATUS_BY_VALUE = {status.value: status for status in JOB_STATUSES}


def get_statuses() -> list[JobStatus]:
    """Restituisce tutti gli stati disponibili."""

    return JOB_STATUSES


def get_status_label(value: str) -> str:
    """Restituisce l'etichetta leggibile di uno stato."""

    status = JOB_STATUS_BY_VALUE.get(value)
    return status.label if status else value


def is_valid_status(value: str) -> bool:
    """Verifica se uno stato è supportato da Radar."""

    return value in JOB_STATUS_BY_VALUE
