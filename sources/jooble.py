"""Connettore Jooble.

Jooble resta la fonte principale per annunci locali italiani. Il connettore
restituisce dizionari normalizzati compatibili con il resto di Radar Lavoro.
"""

from __future__ import annotations

from typing import Any

import requests

from services.text_service import normalize_text


REGION_QUERY_BY_CITY = {
    "angri": "Campania",
    "castel san giorgio": "Campania",
    "castellammare di stabia": "Campania",
    "cava de tirreni": "Campania",
    "cava de' tirreni": "Campania",
    "napoli": "Campania",
    "nocera inferiore": "Campania",
    "nocera superiore": "Campania",
    "pagani": "Campania",
    "pompei": "Campania",
    "pontecagnano faiano": "Campania",
    "roccapiemonte": "Campania",
    "salerno": "Campania",
    "san marzano sul sarno": "Campania",
    "san valentino torio": "Campania",
    "sarno": "Campania",
    "scafati": "Campania",
    "torre annunziata": "Campania",
}


class JoobleSource:
    """Fonte annunci Jooble."""

    name = "Jooble"
    url_template = "https://it.jooble.org/api/{key}"

    def search(self, keyword: str, profile: dict[str, Any]) -> list[dict[str, Any]]:
        api_key = profile.get("jooble_api_key")
        if not api_key:
            return []

        payload: dict[str, Any] = {
            "keywords": keyword,
            "location": self._resolve_source_location(profile),
        }

        distance = str(profile.get("distance_km") or "")
        if distance.isdigit():
            payload["radius"] = distance

        try:
            response = requests.post(
                self.url_template.format(key=api_key),
                json=payload,
                timeout=20,
            )
            response.raise_for_status()
        except requests.RequestException:
            return []

        jobs = response.json().get("jobs", [])[:50]
        return [self._normalize_job(job) for job in jobs]

    def _resolve_source_location(self, profile: dict[str, Any]) -> str:
        """Sceglie la località più coerente da inviare a Jooble.

        Se l'utente sceglie tutta la regione, inviare a Jooble la città di
        partenza produrrebbe risultati molto diversi tra Salerno, Napoli e
        Campania. In quel caso usiamo la regione, così la ricerca è coerente.
        """

        location = str(profile.get("location") or "")
        distance = str(profile.get("distance_km") or "")
        normalized_location = normalize_text(location)

        if distance == "region":
            return REGION_QUERY_BY_CITY.get(normalized_location, location)

        return location

    def _normalize_job(self, job: dict[str, Any]) -> dict[str, Any]:
        return {
            "title": job.get("title") or "Senza titolo",
            "company": job.get("company") or "Azienda non specificata",
            "location": job.get("location") or "",
            "snippet": str(job.get("snippet") or "").replace("&nbsp;", " ").strip(),
            "link": job.get("link") or "",
            "updated": job.get("updated") or "",
            "source": self.name,
        }
