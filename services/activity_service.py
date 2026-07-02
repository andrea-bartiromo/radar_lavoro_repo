"""Attività e timeline della ricerca lavoro.

Ogni azione importante dovrà lasciare una traccia: candidatura inviata,
annuncio preferito, colloquio fissato, follow-up, CV aggiornato e così via.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class ActivityType:
    """Tipo di attività registrabile nella timeline."""

    value: str
    label: str
    icon: str


ACTIVITY_JOB_FOUND = ActivityType("job_found", "Annuncio trovato", "🆕")
ACTIVITY_JOB_SEEN = ActivityType("job_seen", "Annuncio visto", "👀")
ACTIVITY_JOB_FAVORITED = ActivityType("job_favorited", "Annuncio preferito", "⭐")
ACTIVITY_APPLICATION_SENT = ActivityType("application_sent", "Candidatura inviata", "📤")
ACTIVITY_INTERVIEW_SET = ActivityType("interview_set", "Colloquio fissato", "📞")
ACTIVITY_FOLLOW_UP = ActivityType("follow_up", "Follow-up", "🔁")
ACTIVITY_CV_UPDATED = ActivityType("cv_updated", "CV aggiornato", "📄")
ACTIVITY_NOTE_ADDED = ActivityType("note_added", "Nota aggiunta", "📝")
ACTIVITY_REJECTED = ActivityType("rejected", "Scartato", "❌")
ACTIVITY_HIRED = ActivityType("hired", "Assunto", "🎉")

ACTIVITY_TYPES = [
    ACTIVITY_JOB_FOUND,
    ACTIVITY_JOB_SEEN,
    ACTIVITY_JOB_FAVORITED,
    ACTIVITY_APPLICATION_SENT,
    ACTIVITY_INTERVIEW_SET,
    ACTIVITY_FOLLOW_UP,
    ACTIVITY_CV_UPDATED,
    ACTIVITY_NOTE_ADDED,
    ACTIVITY_REJECTED,
    ACTIVITY_HIRED,
]

ACTIVITY_TYPES_BY_VALUE = {activity.value: activity for activity in ACTIVITY_TYPES}


@dataclass(slots=True)
class ActivityEvent:
    """Evento da mostrare nella futura timeline personale."""

    type: str
    title: str
    description: str = ""
    job_id: int | None = None
    company: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="minutes"))
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def type_info(self) -> ActivityType | None:
        """Restituisce le informazioni leggibili del tipo evento."""

        return ACTIVITY_TYPES_BY_VALUE.get(self.type)


def is_valid_activity_type(value: str) -> bool:
    """Verifica se il tipo attività è supportato."""

    return value in ACTIVITY_TYPES_BY_VALUE


def get_activity_label(value: str) -> str:
    """Restituisce l'etichetta leggibile di un tipo attività."""

    activity_type = ACTIVITY_TYPES_BY_VALUE.get(value)
    return activity_type.label if activity_type else value
