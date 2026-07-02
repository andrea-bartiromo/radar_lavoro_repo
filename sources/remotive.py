"""Connettore Remotive.

Remotive pubblica offerte full-remote. È utile per ampliare Radar Lavoro
oltre il solo mercato locale, soprattutto per ruoli digitali e sviluppo web.
"""

from __future__ import annotations

from typing import Any

import requests


class RemotiveSource:
    """Fonte annunci Remotive per lavori da remoto."""

    name = "Remotive"
    url = "https://remotive.com/api/remote-jobs"

    def search(self, keyword: str, profile: dict[str, Any]) -> list[dict[str, Any]]:
        params = {
            "search": keyword,
            "limit": 30,
        }

        try:
            response = requests.get(self.url, params=params, timeout=20)
            response.raise_for_status()
        except requests.RequestException:
            return []

        raw_jobs = response.json().get("jobs", [])
        return [self._normalize_job(job) for job in raw_jobs[:30]]

    def _normalize_job(self, job: dict[str, Any]) -> dict[str, Any]:
        location = job.get("candidate_required_location") or "Remote"

        return {
            "title": job.get("title") or "Senza titolo",
            "company": job.get("company_name") or "Azienda non specificata",
            "location": location,
            "snippet": job.get("description") or "",
            "link": job.get("url") or "",
            "updated": job.get("publication_date") or "",
            "source": self.name,
        }
