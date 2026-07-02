"""Helper condivisi per SQLite.

Questo modulo centralizza la creazione delle connessioni al database. In questo
modo i repository possono usare la stessa configurazione senza duplicare codice.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "radar_lavoro.db"


def get_connection() -> sqlite3.Connection:
    """Apre una connessione SQLite con righe accessibili come dizionari."""

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection
