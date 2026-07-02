"""Gestione centralizzata delle fonti di offerte lavoro.

Il source manager raccoglie annunci da una o più sorgenti e restituisce una
lista normalizzata. Per ora è collegato a Jooble, ma la struttura è pronta per
aggiungere altri connettori senza modificare le route Flask.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(slots=True)
class SourceSearchResult:
    """Risultato normalizzato della raccolta multi-fonte."""

    jobs: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class JobSource(Protocol):
    """Contratto che ogni fonte esterna deve rispettare."""

    name: str

    def search(self, keyword: str, profile: dict) -> list[dict]:
        """Cerca offerte per una keyword e un profilo di ricerca."""


class SourceManager:
    """Orchestra una o più fonti di offerte lavoro."""

    def __init__(self, sources: list[JobSource]) -> None:
        self.sources = sources

    def search_all(self, keywords: list[str], profile: dict) -> SourceSearchResult:
        """Esegue la ricerca su tutte le fonti abilitate."""

        result = SourceSearchResult()

        for keyword in keywords:
            for source in self.sources:
                try:
                    jobs = source.search(keyword, profile)
                except Exception as exc:  # noqa: BLE001 - non blocchiamo l'intera ricerca
                    result.errors.append(f"{source.name}: {exc}")
                    continue

                for job in jobs:
                    job["source"] = source.name
                    job["matched_query"] = keyword
                    result.jobs.append(job)

        return result
