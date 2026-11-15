import psycopg
from psycopg.rows import dict_row

from domain.identity.infrastructure.ports.identity_repository import IdentityRepository
from domain.identity.models.aggregates import User, UserId
from domain.identity.models.value_objects import DisplayName, Email, PasswordHash

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY,
    display_name  TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);
"""


class PostgresIdentityRepository(IdentityRepository):
    """Identity repository persisting users in a PostgreSQL table."""

    def __init__(self, dsn: str, *, create_schema: bool = True) -> None:
        self.conn = psycopg.connect(dsn, row_factory=dict_row, autocommit=True)
        if create_schema:
            self.conn.execute(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    # ---- mapping ----
    @staticmethod
    def _to_user(row: dict) -> User:
        return User(
            id=UserId(row["id"]),
            display_name=DisplayName(row["display_name"]),
            email=Email(row["email"]),
            password_hash=PasswordHash(row["password_hash"]),
        )

    # ---- port implementation ----
    def add_user(self, user: User) -> None:
        self.conn.execute(
            """
            INSERT INTO users (id, display_name, email, password_hash)
            VALUES (%s, %s, %s, %s)
            """,
            (
                str(user.id.value),
                user.display_name.value,
                user.email.value,
                user.password_hash.value,
            ),
        )

    def get_by_id(self, user_id: UserId) -> User | None:
        row = self.conn.execute(
            "SELECT * FROM users WHERE id = %s",
            (str(user_id.value),),
        ).fetchone()
        return self._to_user(row) if row else None

    def get_by_ids(self, user_ids: list[UserId]) -> list[User]:
        if not user_ids:
            return []
        rows = self.conn.execute(
            "SELECT * FROM users WHERE id = ANY(%s::uuid[])",
            ([str(u.value) for u in user_ids],),
        ).fetchall()
        return [self._to_user(r) for r in rows]

    def get_by_email(self, email: Email) -> User | None:
        row = self.conn.execute(
            "SELECT * FROM users WHERE email = %s",
            (email.value,),
        ).fetchone()
        return self._to_user(row) if row else None
