"""Database setup and connection management."""

import sqlite3

from src.api.appointments.models import APPOINTMENTS_TABLE_SCHEMA
from src.api.patients.models import PATIENTS_TABLE_SCHEMA
from src.core.config import Config

# Load config and get database path
config = Config.from_yaml("configs/config.yaml")
DB_PATH = config.paths.data / "online-clinic.db"


def get_connection() -> sqlite3.Connection:
    """Create and return a database connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


def initialize_database() -> None:
    """Create the patients table if it doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(PATIENTS_TABLE_SCHEMA)
    cursor.execute(APPOINTMENTS_TABLE_SCHEMA)

    conn.commit()
    conn.close()


# Initialize database on module import
if __name__ == "__main__":
    initialize_database()
