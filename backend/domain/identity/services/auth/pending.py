"""Single-use server-side OAuth authorization attempts."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from psycopg import Connection
    from pymongo.collection import Collection

from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from threading import Lock

ATTEMPT_LIFETIME = timedelta(minutes=5)


class PendingAttempts:
    """Store attempts in development memory or a shared Mongo collection."""

    def __init__(self, collection: "Collection | None" = None) -> None:
        """Set up the pending store and its expiry index."""
        self.collection = collection
        self.items: dict[str, dict] = {}
        self.lock = Lock()
        if collection is not None:
            collection.create_index("expires", expireAfterSeconds=0)

    def put(self, attempt: dict) -> str:
        """Save the expiring request and return its opaque identifier."""
        key = token_urlsafe(32)
        now = datetime.now(UTC)
        attempt = dict(attempt, expires=now + ATTEMPT_LIFETIME)
        if self.collection is not None:
            self.collection.insert_one(dict(attempt, _id=key))
        else:
            with self.lock:
                self.items = {k: v for k, v in self.items.items() if v["expires"] > now}
                self.items[key] = attempt
        return key

    def take(self, key: str | None) -> dict | None:
        """Atomically remove and return the pending request."""
        if not key:
            return None
        if self.collection is not None:
            return self.collection.find_one_and_delete({"_id": key})
        with self.lock:
            return self.items.pop(key, None)


class PostgresPendingAttempts:
    """Coordinate single-use callbacks between workers sharing an identity database."""

    def __init__(self, connection: "Connection[dict]") -> None:
        """Initialize durable request storage."""
        self.connection = connection
        connection.execute("""
            CREATE TABLE IF NOT EXISTS oauth_attempts (
                id TEXT PRIMARY KEY, expires TIMESTAMPTZ NOT NULL, attempt JSONB NOT NULL
            )
        """)

    def put(self, attempt: dict) -> str:
        """Save the expiring request and return its opaque identifier."""
        from psycopg.types.json import Jsonb

        key = token_urlsafe(32)
        self.connection.execute("DELETE FROM oauth_attempts WHERE expires <= now()")
        self.connection.execute(
            "INSERT INTO oauth_attempts VALUES (%s, now() + %s, %s)",
            (key, ATTEMPT_LIFETIME, Jsonb(attempt)),
        )
        return key

    def take(self, key: str | None) -> dict | None:
        """Atomically remove and return the pending request."""
        if not key:
            return None
        row = self.connection.execute(
            "DELETE FROM oauth_attempts WHERE id = %s RETURNING attempt, expires", (key,)
        ).fetchone()
        return dict(row["attempt"], expires=row["expires"]) if row else None
