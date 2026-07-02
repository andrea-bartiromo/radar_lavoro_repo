"""Connettore Jooble.

Jooble resta la fonte principale per annunci locali italiani. Il connettore
restituisce dizionari normalizzati compatibili con il resto di Radar Lavoro.
"""

from __future__ import annotations

from typing import Any

import requests


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
            "location": profile.get("location", ""),
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
