"""Diagnostica della ricerca.

Il servizio costruisce riepiloghi leggibili a partire dalle statistiche della
pipeline. Verrà usato dalla futura pagina /diagnostica.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from services.pipeline_service import PipelineStats


@dataclass(slots=True)
class DiagnosticItem:
    """Singola riga del riepilogo diagnostico."""

    label: str
    value: int
    description: str = ""


@dataclass(slots=True)
class DiagnosticReport:
    """Report diagnostico pronto per template o log."""

    total_collected: int
    total_saved: int
    source_items: list[DiagnosticItem] = field(default_factory=list)
    filter_items: list[DiagnosticItem] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        """Indica se durante la ricerca ci sono stati errori di fonte."""

        return bool(self.errors)


def build_diagnostic_report(stats: PipelineStats) -> DiagnosticReport:
    """Converte le statistiche della pipeline in un report leggibile."""

    source_items = [
        DiagnosticItem(label=source, value=count, description="Annunci raccolti dalla fonte")
        for source, count in sorted(stats.source_totals.items())
    ]

    filter_items = [
        DiagnosticItem(
            label="Filtro geografico",
            value=stats.rejected_by_geo,
            description="Annunci esclusi perché fuori area",
        ),
        DiagnosticItem(
            label="Filtro profilo",
            value=stats.rejected_by_profile,
            description="Annunci esclusi perché poco coerenti",
        ),
        DiagnosticItem(
            label="Duplicati",
            value=stats.rejected_as_duplicate,
            description="Annunci equivalenti già presenti",
        ),
    ]

    return DiagnosticReport(
        total_collected=stats.collected,
        total_saved=stats.saved,
        source_items=source_items,
        filter_items=filter_items,
        errors=list(stats.errors),
    )
