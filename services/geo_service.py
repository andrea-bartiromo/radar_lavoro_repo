"""Servizio geografico per località, province e distanze.

Questo modulo contiene la logica geografica che prima era dentro app.py.
Serve a decidere se un annuncio rientra nell'area scelta dall'utente.
"""

from __future__ import annotations

import math

from services.text_service import normalize_text


CITY_COORDS: dict[str, tuple[float, float]] = {
    "nocera inferiore": (40.7454, 14.6410),
    "nocera superiore": (40.7421, 14.6746),
    "pagani": (40.7410, 14.6140),
    "angri": (40.7382, 14.5708),
    "scafati": (40.7464, 14.5296),
    "sant antonio abate": (40.7212, 14.5405),
    "sant'antonio abate": (40.7212, 14.5405),
    "san marzano sul sarno": (40.7780, 14.5844),
    "san valentino torio": (40.7929, 14.6022),
    "sarno": (40.8104, 14.6194),
    "roccapiemonte": (40.7610, 14.6923),
    "castel san giorgio": (40.7817, 14.6990),
    "cava de tirreni": (40.7019, 14.7046),
    "cava de' tirreni": (40.7019, 14.7046),
    "pompei": (40.7460, 14.4977),
    "salerno": (40.6824, 14.7681),
    "pontecagnano faiano": (40.6435, 14.8730),
    "castellammare di stabia": (40.6954, 14.4806),
    "torre annunziata": (40.7537, 14.4527),
    "ottaviano": (40.8512, 14.4783),
    "napoli": (40.8518, 14.2681),
    "brescia": (45.5416, 10.2118),
}

CITY_PROVINCES: dict[str, str] = {
    "salerno": "SA",
    "nocera inferiore": "SA",
    "nocera superiore": "SA",
    "pagani": "SA",
    "angri": "SA",
    "scafati": "SA",
    "sarno": "SA",
    "cava de tirreni": "SA",
    "cava de' tirreni": "SA",
    "pontecagnano faiano": "SA",
    "castel san giorgio": "SA",
    "roccapiemonte": "SA",
    "san marzano sul sarno": "SA",
    "san valentino torio": "SA",
    "pompei": "NA",
    "castellammare di stabia": "NA",
    "torre annunziata": "NA",
    "ottaviano": "NA",
    "napoli": "NA",
    "brescia": "BS",
}

PROVINCE_CODES = "sa|na|av|bn|ce|bs"


def extract_city(location: str) -> str:
    """Estrae una città nota da una località libera."""

    text = normalize_text(location)
    if not text:
        return ""

    for city in sorted(CITY_COORDS, key=len, reverse=True):
        if city in text:
            return city

    return " ".join(text.split()[:3])


def get_province(city: str) -> str | None:
    """Restituisce la provincia associata alla città, se nota."""

    return CITY_PROVINCES.get(normalize_text(city))


def calculate_distance_km(city_a: str, city_b: str) -> float | None:
    """Calcola la distanza approssimativa tra due città note."""

    coords_a = CITY_COORDS.get(normalize_text(city_a))
    coords_b = CITY_COORDS.get(normalize_text(city_b))

    if not coords_a or not coords_b:
        return None

    lat_a, lon_a = map(math.radians, coords_a)
    lat_b, lon_b = map(math.radians, coords_b)

    delta_lat = lat_b - lat_a
    delta_lon = lon_b - lon_a

    haversine = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat_a) * math.cos(lat_b) * math.sin(delta_lon / 2) ** 2
    )

    return 6371 * 2 * math.asin(math.sqrt(haversine))


def is_within_search_area(search_location: str, job_location: str, radius: str) -> bool:
    """Verifica se la località dell'annuncio rientra nell'area impostata."""

    search_city = extract_city(search_location)
    job_city = extract_city(job_location)

    if not search_city or not job_city:
        return True

    if radius == "region":
        return True

    if radius == "province":
        return get_province(search_city) == get_province(job_city)

    if not radius:
        return job_city == search_city

    if not radius.isdigit():
        return True

    distance = calculate_distance_km(search_city, job_city)
    if distance is None:
        return job_city == search_city

    return distance <= float(radius)
