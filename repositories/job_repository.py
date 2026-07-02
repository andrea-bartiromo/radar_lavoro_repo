"""Repository annunci.

Questo modulo ospiterà progressivamente tutta la logica di accesso alla tabella
jobs. Per ora contiene lo scheletro pubblico usato come contratto architetturale.
"""

from __future__ import annotations

from typing import Any


class JobRepository:
    """Contratto del repository degli annunci."""

    def list_for_dashboard(self, search_location: str, limit: int = 150) -> list[dict[str, Any]]:
        """Restituirà gli annunci da mostrare nella dashboard."""

        raise NotImplementedError

    def mark_as_seen(self, job_id: int, search_location: str) -> None:
        """Marcherà un annuncio come già visto."""

        raise NotImplementedError

    def mark_all_as_seen(self, search_location: str) -> None:
        """Marcherà come già visti tutti gli annunci dell'area corrente."""

        raise NotImplementedError
