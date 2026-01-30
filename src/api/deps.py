"""FastAPI dependencies for dependency injection."""

from collections.abc import Generator
from sqlite3 import Connection

from .database import get_connection


def get_db() -> Generator[Connection, None, None]:
    """
    Dependency for getting database connection.

    Yields:
        Connection: SQLite database connection

    Example:
        @app.get("/items")
        def get_items(db: Connection = Depends(get_db)):
            cursor = db.cursor()
            # ... use cursor
    """
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
