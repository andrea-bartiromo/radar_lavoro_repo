"""Pipeline di ricerca annunci.

La pipeline definisce l'ordine logico con cui Radar Lavoro dovrà trattare gli
annunci raccolti dalle fonti esterne.

Fasi previste:

1. raccolta dalle fonti;
2. normalizzazione;
3. filtro geografico;
4. filtro professionale;
5. deduplicazione;
6. matching;
7. ranking;
8. salvataggio;
9. diagnostica.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PipelineStats:
    """Statistiche prodotte da una ricerca."""

    collected: int = 0
    rejected_by_geo: int = 0
    rejected_by_profile: int = 0
    rejected_as_duplicate: int = 0
    saved: int = 0
    source_totals: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def final_results(self) -> int:
        """Numero di risultati arrivati alla dashboard."""

        return self.saved


@dataclass(slots=True)
class PipelineResult:
    """Risultato finale della pipeline."""

    jobs: list[dict[str, Any]] = field(default_factory=list)
    stats: PipelineStats = field(default_factory=PipelineStats)


class SearchPipeline:
    """Contratto della pipeline di ricerca.

    L'implementazione completa verrà collegata dopo aver spostato l'accesso al
    database nei repository.
    """

    def run(self, profile: dict[str, Any]) -> PipelineResult:
        """Eseguirà la ricerca completa per il profilo fornito."""

        raise NotImplementedError
