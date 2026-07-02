"""Repository attività.

Questo modulo gestirà la futura timeline della ricerca lavoro.
Ogni azione importante dovrà essere registrata come evento consultabile.
"""

from __future__ import annotations

from services.activity_service import ActivityEvent


class ActivityRepository:
    """Contratto per salvare e leggere eventi della timeline."""

    def add_event(self, event: ActivityEvent) -> None:
        """Salverà un nuovo evento nella timeline."""

        raise NotImplementedError

    def list_recent(self, limit: int = 50) -> list[ActivityEvent]:
        """Restituirà gli eventi più recenti della ricerca lavoro."""

        raise NotImplementedError
