"""Matching tra annunci e profilo professionale.

Questo modulo contiene le regole che stabiliscono se un annuncio è pertinente
rispetto alle ricerche impostate e al profilo personale.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from services.profile_service import get_profile_matching_terms
from services.text_service import build_job_text, contains_any, count_matches, normalize_text


ENTRY_TERMS = [
    "junior",
    "stage",
    "tirocinio",
    "entry level",
    "neolaureato",
    "neolaureata",
    "apprendistato",
    "prima esperienza",
]

SENIOR_TERMS = [
    "senior",
    "lead",
    "responsabile",
    "head of",
    "coordinator",
    "coordinatore",
    "manager",
    "team lead",
]

HARD_BLOCK_TERMS = [
    "patent attorney",
    "mandatario brevetti",
    "brevetti",
    "agente plurimandatario",
    "ragazze immagine",
    "fotomodell",
    "casting",
    "call center",
    "telemarketing",
    "operatore outbound",
]

GLOBAL_NEGATIVE_TERMS = [
    "agente plurimandatario",
    "agenti plurimandatari",
    "key account",
    "procacciatore",
    "plc",
    "bricolage",
    "ferramenta",
    "casalinghi",
    "patent attorney",
    "mandatario brevetti",
    "brevetti",
    "telemarketing",
    "call center",
    "operatore outbound",
]

QUERY_PROFILES = {
    "comunicazione digitale": {
        "positive": [
            "comunicaz",
            "digital",
            "marketing",
            "content",
            "social",
            "media",
            "grafica",
            "adv",
            "seo",
            "copy",
        ],
        "strong": [
            "comunicazione",
            "digital marketing",
            "social media",
            "content",
            "ufficio stampa",
            "seo",
            "copy",
        ],
        "negative": ["telemarketing", "call center", "outbound", "vendite", "sales"],
    },
    "social media manager": {
        "positive": [
            "social",
            "media",
            "instagram",
            "facebook",
            "tiktok",
            "community",
            "content",
            "creator",
            "meta",
        ],
        "strong": ["social media", "community", "instagram", "facebook", "tiktok", "meta"],
        "negative": ["key account", "commerciale", "sales", "vendite", "telemarketing"],
    },
    "content creator": {
        "positive": ["content", "creator", "contenut", "video", "storytelling", "social"],
        "strong": ["content creator", "contenuti", "storytelling", "social"],
        "negative": ["ragazza", "ragazze immagine", "casting", "fotomodell"],
    },
    "copywriter": {
        "positive": ["copy", "copywriter", "redatt", "testi", "scrittura", "contenut"],
        "strong": ["copywriter", "redattore", "redattrice", "testi", "scrittura"],
        "negative": [],
    },
    "giornalista redattore": {
        "positive": ["giornal", "redatt", "redazione", "editor", "stampa"],
        "strong": ["giornalista", "redattore", "redattrice", "redazione", "editor"],
        "negative": [],
    },
    "ufficio stampa": {
        "positive": ["stampa", "press", "comunicaz", "media relation", "pr"],
        "strong": ["ufficio stampa", "press", "media relation", "pr", "comunicazione"],
        "negative": [],
    },
    "data analyst junior": {
        "positive": [
            "data",
            "analyst",
            "analista",
            "dati",
            "analytics",
            "report",
            "dashboard",
            "python",
            "sql",
            "excel",
        ],
        "strong": [
            "data analyst",
            "analista dati",
            "business analyst",
            "analytics",
            "python",
            "sql",
            "dashboard",
            "report",
        ],
        "negative": [
            "agente",
            "plurimandatario",
            "commerciale",
            "brevetti",
            "patent",
            "attorney",
            "mandatario",
            "meccatronica",
            "elettronica",
        ],
    },
    "web developer junior": {
        "positive": [
            "developer",
            "svilupp",
            "programmat",
            "web",
            "python",
            "javascript",
            "html",
            "css",
            "wordpress",
            ".net",
            "java",
            "software",
        ],
        "strong": [
            "web developer",
            "software developer",
            "sviluppatore",
            "developer",
            "programmatore",
            "python",
            "javascript",
            ".net",
            "java",
            "wordpress",
        ],
        "negative": ["plc", "pharma", "commerciale", "key account", "sales", "agente"],
    },
}


@dataclass(slots=True)
class MatchResult:
    """Risultato del confronto tra annuncio e profilo."""

    is_relevant: bool
    relevance_score: int
    profile_matches: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


def has_hard_block(job: dict[str, Any], query: str = "") -> bool:
    """Esclude ruoli chiaramente fuori profilo."""

    text = normalize_text(build_job_text(job))

    if contains_any(text, HARD_BLOCK_TERMS):
        return True

    if "data analyst" in query.lower():
        return contains_any(text, ["brevetti", "patent", "attorney", "meccatronica", "elettronica"])

    return False


def calculate_relevance_score(job: dict[str, Any], query: str) -> int:
    """Calcola quanto l'annuncio è pertinente rispetto a una keyword."""

    normalized_query = query.lower().strip()
    text = normalize_text(build_job_text(job))
    title = normalize_text(job.get("title"))

    if has_hard_block(job, normalized_query):
        return 0

    query_profile = QUERY_PROFILES.get(normalized_query)
    if query_profile is None:
        terms = [word for word in normalize_text(query).split() if len(word) > 3]
        return min(100, sum(18 for term in terms if term in text))

    if contains_any(text, query_profile.get("negative", []) + GLOBAL_NEGATIVE_TERMS):
        return 0

    positive_hits = count_matches(text, query_profile["positive"])
    strong_hits = count_matches(text, query_profile["strong"])
    title_hits = count_matches(title, query_profile["positive"])

    if positive_hits == 0:
        return 0

    if normalized_query in {"data analyst junior", "web developer junior"}:
        if strong_hits == 0 and title_hits == 0:
            return 0

    if normalized_query in {"comunicazione digitale", "social media manager", "content creator"}:
        if strong_hits == 0 and positive_hits < 2:
            return 0

    return min(100, positive_hits * 12 + strong_hits * 18 + title_hits * 10)


def match_job(job: dict[str, Any], query: str, exclude_keywords: list[str]) -> MatchResult:
    """Valuta se un annuncio è pertinente e perché."""

    text = normalize_text(build_job_text(job))
    title = normalize_text(job.get("title"))
    reasons: list[str] = []

    for term in exclude_keywords:
        normalized_term = normalize_text(term)
        if normalized_term and (normalized_term in title or normalized_term in text):
            return MatchResult(
                is_relevant=False,
                relevance_score=0,
                reasons=[f"escluso per parola: {term}"],
            )

    relevance = calculate_relevance_score(job, query)
    if relevance >= 70:
        reasons.append("molto pertinente")
    elif relevance >= 24:
        reasons.append("pertinente")

    profile_matches = [term for term in get_profile_matching_terms() if term in text]
    if profile_matches:
        reasons.append("profilo coerente")

    return MatchResult(
        is_relevant=relevance >= 24,
        relevance_score=relevance,
        profile_matches=profile_matches,
        reasons=reasons,
    )
