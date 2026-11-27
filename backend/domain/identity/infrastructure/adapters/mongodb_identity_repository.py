import json
from typing import Any
from uuid import UUID

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from domain.identity.infrastructure.ports.identity_repository import (
    IdentityConflict,
    IdentityRepository,
)
from domain.identity.models.aggregates import User
from domain.identity.models.value_objects import (
    DisplayName,
    Email,
    PasswordHash,
    UserId,
)
from domain.identity.services.auth.errors import EmailAlreadyRegisteredError


class MongoIdentityRepository(IdentityRepository):
    """Identity repository persisting users in a MongoDB collection."""

    def __init__(
        self,
        uri: str = "mongodb://localhost:27017",
        db_name: str = "mydb",
        *,
        collection: str = "users",
    ) -> None:
        """Initialize the adapter and its dependencies."""
        self.client: MongoClient[dict[str, Any]] = MongoClient(uri)
        self.users = self.client[db_name][collection]
        owners = {}
        for doc in self.users.find({}, {"email": 1}):
            key = doc["email"].casefold()
            if key in owners:
                raise ValueError("Resolve duplicate normalized emails before migration")
            owners[key] = doc["_id"]
        for key, uid in owners.items():
            self.users.update_one(
                {"_id": uid, "email_key": {"$ne": key}}, {"$set": {"email_key": key}}
            )
        for key in ("email_key", "identities.key"):
            self.users.create_index(
                key, unique=True, partialFilterExpression={key: {"$type": "string"}}
            )

    def close(self) -> None:
        """Close the database connection."""
        self.client.close()

    # ---- mapping ----
    @staticmethod
    def _to_doc(user: User) -> dict:
        return {
            "_id": str(user.id.value),
            "display_name": user.display_name.value,
            "email": user.email.value,
            "email_key": user.email.value.casefold(),
            "verified": user.verified,
            "status": user.status,
            "password_hash": user.password_hash.value if user.password_hash else None,
        }

    @staticmethod
    def _to_user(doc: dict) -> User:
        return User(
            id=UserId(UUID(doc["_id"])),
            display_name=DisplayName(doc["display_name"]),
            email=Email(doc["email"]),
            password_hash=PasswordHash(doc["password_hash"]) if doc.get("password_hash") else None,
            verified=doc.get("verified", False),
            status=doc.get("status", "active"),
        )

    # ---- port implementation ----
    def add_user(self, user: User) -> User | None:
        """Store the user in the repository."""
        try:
            self.users.insert_one(self._to_doc(user))
        except DuplicateKeyError as exc:
            raise EmailAlreadyRegisteredError() from exc
        return user

    def get_by_id(self, user_id: UserId) -> User | None:
        """Return the user with the given ID, or None."""
        doc = self.users.find_one({"_id": str(user_id.value)})
        return self._to_user(doc) if doc else None

    def get_by_ids(self, user_ids: list[UserId]) -> list[User]:
        """Return users matching the given IDs."""
        if not user_ids:
            return []
        docs = self.users.find({"_id": {"$in": [str(u.value) for u in user_ids]}})
        return [self._to_user(d) for d in docs]

    def get_by_email(self, email: Email) -> User | None:
        """Return the user with the given email, or None."""
        doc = self.users.find_one({"email_key": email.value.casefold()})
        return self._to_user(doc) if doc else None

    def has_identity(self, user_id: UserId, issuer: str) -> bool:
        """Return whether the account owns an identity from this issuer."""
        doc = self.users.find_one({"_id": str(user_id.value)}, {"identities.key": 1})
        return any(
            json.loads(item["key"])[0] == issuer for item in (doc or {}).get("identities", [])
        )

    def find_identity(self, issuer: str, subject: str) -> User | None:
        """Load the owner of the issuer and subject pair."""
        doc = self.users.find_one({"identities.key": json.dumps([issuer, subject])})
        return self._to_user(doc) if doc else None

    def provision(self, user: User, issuer: str, subject: str) -> None:
        """Create the account and identity together."""
        doc = self._to_doc(user)
        doc["identities"] = [{"key": json.dumps([issuer, subject])}]
        try:
            self.users.insert_one(doc)
        except DuplicateKeyError as exc:
            raise IdentityConflict() from exc

    def link(self, user: User, issuer: str, subject: str) -> None:
        """Attach the identity only if the account can own it."""
        try:
            result = self.users.update_one(
                {"_id": str(user.id.value)},
                {"$addToSet": {"identities": {"key": json.dumps([issuer, subject])}}},
            )
            if not result.matched_count:
                raise IdentityConflict()
        except DuplicateKeyError as exc:
            raise IdentityConflict() from exc

    def rename(self, user: User, name: str) -> None:
        """Persist the validated display name."""
        self.users.update_one({"_id": str(user.id.value)}, {"$set": {"display_name": name}})
