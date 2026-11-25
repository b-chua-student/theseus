import psycopg
from psycopg.rows import dict_row

from domain.identity.infrastructure.ports.identity_repository import (
    IdentityConflict,
    IdentityRepository,
)
from domain.identity.models.aggregates import User, UserId
from domain.identity.models.value_objects import DisplayName, Email, PasswordHash
from domain.identity.services.auth.errors import EmailAlreadyRegisteredError

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY,
    display_name  TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);
ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS verified BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active';
CREATE UNIQUE INDEX IF NOT EXISTS users_email_normalized ON users(lower(email));
CREATE TABLE IF NOT EXISTS external_identities (
    issuer TEXT NOT NULL, subject TEXT NOT NULL, user_id UUID NOT NULL REFERENCES users(id),
    PRIMARY KEY (issuer, subject)
);
"""


class PostgresIdentityRepository(IdentityRepository):
    """Identity repository persisting users in a PostgreSQL table."""

    def __init__(self, dsn: str, *, create_schema: bool = True) -> None:
        """Initialize the adapter and its dependencies."""
        self.dsn = dsn
        self.conn = psycopg.connect(dsn, row_factory=dict_row, autocommit=True)
        if create_schema:
            self.conn.execute(SCHEMA)

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()

    # ---- mapping ----
    @staticmethod
    def _to_user(row: dict) -> User:
        return User(
            id=UserId(row["id"]),
            display_name=DisplayName(row["display_name"]),
            email=Email(row["email"]),
            password_hash=PasswordHash(row["password_hash"]) if row["password_hash"] else None,
            verified=row["verified"],
            status=row["status"],
        )

    # ---- port implementation ----
    def add_user(self, user: User) -> None:
        """Store the user in the repository."""
        try:
            self._insert_user(self.conn, user)
        except psycopg.errors.UniqueViolation as exc:
            raise EmailAlreadyRegisteredError() from exc

    @staticmethod
    def _insert_user(connection: psycopg.Connection[dict], user: User) -> None:
        connection.execute(
            """
            INSERT INTO users (id, display_name, email, password_hash, verified, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                str(user.id.value),
                user.display_name.value,
                user.email.value,
                user.password_hash.value if user.password_hash else None,
                user.verified,
                user.status,
            ),
        )

    def get_by_id(self, user_id: UserId) -> User | None:
        """Return the user with the given ID, or None."""
        row = self.conn.execute(
            "SELECT * FROM users WHERE id = %s",
            (str(user_id.value),),
        ).fetchone()
        return self._to_user(row) if row else None

    def get_by_ids(self, user_ids: list[UserId]) -> list[User]:
        """Return users matching the given IDs."""
        if not user_ids:
            return []
        rows = self.conn.execute(
            "SELECT * FROM users WHERE id = ANY(%s::uuid[])",
            ([str(u.value) for u in user_ids],),
        ).fetchall()
        return [self._to_user(r) for r in rows]

    def get_by_email(self, email: Email) -> User | None:
        """Return the user with the given email, or None."""
        row = self.conn.execute(
            "SELECT * FROM users WHERE lower(email) = lower(%s)",
            (email.value,),
        ).fetchone()
        return self._to_user(row) if row else None

    def find_identity(self, issuer: str, subject: str) -> User | None:
        """Load the owner of the issuer and subject pair."""
        row = self.conn.execute(
            "SELECT u.* FROM users u JOIN external_identities e ON e.user_id=u.id "
            "WHERE issuer=%s AND subject=%s",
            (issuer, subject),
        ).fetchone()
        return self._to_user(row) if row else None

    def provision(self, user: User, issuer: str, subject: str) -> None:
        """Create the account and identity together."""
        try:
            with psycopg.connect(self.dsn, row_factory=dict_row) as connection:
                self._insert_user(connection, user)
                connection.execute(
                    "INSERT INTO external_identities VALUES (%s,%s,%s)",
                    (issuer, subject, user.id.value),
                )
        except psycopg.errors.UniqueViolation as exc:
            raise IdentityConflict() from exc

    def link(self, user: User, issuer: str, subject: str) -> None:
        """Attach the identity only if the account can own it."""
        self.conn.execute(
            "INSERT INTO external_identities VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
            (issuer, subject, user.id.value),
        )
        if self.find_identity(issuer, subject) != user:
            raise IdentityConflict()

    def rename(self, user: User, name: str) -> None:
        """Persist the validated display name."""
        self.conn.execute("UPDATE users SET display_name=%s WHERE id=%s", (name, user.id.value))
