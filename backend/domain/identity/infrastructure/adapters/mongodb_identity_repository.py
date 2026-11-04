from uuid import UUID

from pymongo import MongoClient

from domain.identity.infrastructure.ports.identity_repository import IdentityRepository
from domain.identity.models.aggregates import User
from domain.identity.models.value_objects import (
    DisplayName,
    Email,
    PasswordHash,
    UserId,
)


class MongoIdentityRepository(IdentityRepository):
    """Identity repository persisting users in a MongoDB collection."""

    def __init__(
        self,
        uri: str = "mongodb://localhost:27017",
        db_name: str = "mydb",
        *,
        collection: str = "users",
    ) -> None:
        self.client = MongoClient(uri)
        self.users = self.client[db_name][collection]
        self.users.create_index("email", unique=True)

    def close(self) -> None:
        self.client.close()

    # ---- mapping ----
    @staticmethod
    def _to_doc(user: User) -> dict:
        return {
            "_id": str(user.id.value),
            "display_name": user.display_name.value,
            "email": user.email.value,
            "password_hash": user.password_hash.value,
        }

    @staticmethod
    def _to_user(doc: dict) -> User:
        return User(
            id=UserId(UUID(doc["_id"])),
            display_name=DisplayName(doc["display_name"]),
            email=Email(doc["email"]),
            password_hash=PasswordHash(doc["password_hash"]),
        )

    # ---- port implementation ----
    def add_user(self, user: User) -> User | None:
        self.users.insert_one(self._to_doc(user))
        return user

    def get_by_id(self, user_id: UserId) -> User | None:
        doc = self.users.find_one({"_id": str(user_id.value)})
        return self._to_user(doc) if doc else None

    def get_by_ids(self, user_ids: list[UserId]) -> list[User]:
        if not user_ids:
            return []
        docs = self.users.find({"_id": {"$in": [str(u.value) for u in user_ids]}})
        return [self._to_user(d) for d in docs]

    def get_by_email(self, email: Email) -> User | None:
        doc = self.users.find_one({"email": email.value})
        return self._to_user(doc) if doc else None
