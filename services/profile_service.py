"""Profilo professionale personale usato dal motore di matching.

Per ora il profilo è definito in modo statico perché Radar Lavoro è pensato per
l'uso personale. In seguito potrà essere salvato nel database e aggiornato
automaticamente leggendo il CV.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PersonalProfile:
    """Rappresenta il profilo professionale principale dell'utente."""

    name: str
    headline: str
    location: str
    protected_category: str
    degree: str
    master: str
    languages: list[str] = field(default_factory=list)
    mobility: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    target_roles: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)

    @property
    def matching_terms(self) -> list[str]:
        """Restituisce i termini da usare nel ranking degli annunci."""

        base_terms = [
            self.degree,
            self.master,
            self.protected_category,
            *self.skills,
            *self.target_roles,
            *self.certifications,
        ]

        return sorted({term.lower() for term in base_terms if term})

    def to_template_context(self) -> dict[str, object]:
        """Converte il profilo in un dizionario comodo per i template Jinja."""

        return {
            "name": self.name,
            "headline": self.headline,
            "location": self.location,
            "protected_category": self.protected_category,
            "degree": self.degree,
            "master": self.master,
            "languages": self.languages,
            "mobility": self.mobility,
            "skills": self.skills,
            "target_roles": self.target_roles,
            "certifications": self.certifications,
        }


PERSONAL_PROFILE = PersonalProfile(
    name="Andrea Bartiromo",
    headline="Junior Full Stack Web Developer · Digital & Communication Specialist",
    location="Nocera Inferiore",
    protected_category="Categorie protette L.68/99",
    degree="Laurea triennale in Scienze della Comunicazione",
    master="LM-92 in corso — conseguimento previsto entro i primi mesi del 2027",
    languages=[
        "Italiano madrelingua",
        "Inglese B1",
    ],
    mobility=[
        "Patente B",
        "Automunito",
        "Disponibilità area Campania / remoto",
    ],
    skills=[
        "Comunicazione digitale",
        "Corporate Communication",
        "Giornalismo",
        "Redazione",
        "Fact-checking",
        "Social media",
        "Content creation",
        "Copywriting",
        "Storytelling",
        "Ufficio stampa",
        "SEO",
        "SEM",
        "Web analytics",
        "Meta Business Suite",
        "Canva",
        "LinkedIn",
        "HTML",
        "CSS",
        "JavaScript",
        "PHP",
        "Laravel",
        "Python",
        "MySQL",
        "SQL",
        "API REST",
        "Git",
        "GitHub",
        "Postman",
        "React base",
        "Cybersecurity basics",
        "Data analysis",
        "AI basics",
    ],
    target_roles=[
        "Digital Communication Specialist",
        "Social Media Specialist",
        "Content Specialist",
        "Junior Web Developer",
        "Junior Full Stack Developer",
        "Data Analyst Junior",
        "Redattore",
        "Ufficio stampa junior",
    ],
    certifications=[
        "Data Analyst — Fondazione Mondo Digitale",
        "Sicurezza Informatica — Cisco",
        "AI Avanzata — Profession AI",
        "Python — Profession AI",
        "EIPASS 7 Moduli User",
        "Hackademy+ Aulab — Full Stack Web Developer",
    ],
)


def get_personal_profile() -> PersonalProfile:
    """Restituisce il profilo personale attivo."""

    return PERSONAL_PROFILE


def get_profile_matching_terms() -> list[str]:
    """Restituisce i termini normalizzati usati dal motore di compatibilità."""

    return PERSONAL_PROFILE.matching_terms
