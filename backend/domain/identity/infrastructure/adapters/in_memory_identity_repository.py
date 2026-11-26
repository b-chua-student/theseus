from threading import RLock

from faker import Faker

from domain.identity.infrastructure.adapters.argon_password_hasher import ArgonPasswordHasher
from domain.identity.infrastructure.ports.identity_repository import (
    IdentityConflict,
    IdentityRepository,
)
from domain.identity.models.aggregates import User, UserId
from domain.identity.models.value_objects import DisplayName, Email, PasswordHash
from domain.identity.services.auth.errors import EmailAlreadyRegisteredError


class InMemoryIdentityRepository(IdentityRepository):
    """Identity repository that keeps users in a list, optionally seeded with fake users."""

    def __init__(self, *, seed: bool = False, totalUsers: int = 5) -> None:
        """Initialize the adapter and its dependencies."""
        self.db: list[User] = []
        self.lock = RLock()
        self.identities: dict[tuple[str, str], User] = {}
        self.fake = Faker()
        self.hasher = ArgonPasswordHasher()
        if seed:
            self.seed(totalUsers=totalUsers)

    def seed(self, totalUsers: int) -> None:
        """Populate the repository with generated users and a test user."""
        for _i in range(totalUsers):
            self.db.append(
                User(
                    id=UserId.new(),
                    display_name=DisplayName(self.fake.name()),
                    email=Email(self.fake.email()),
                    password_hash=PasswordHash(self.hasher.hash(self.fake.password())),
                )
            )

        constant_user = User(
            id=UserId.new(),
            display_name=DisplayName("Test User"),
            email=Email("test@example.com"),
            password_hash=PasswordHash(self.hasher.hash("password")),
        )

        self.db.append(constant_user)

    def add_user(self, user: User) -> None:
        """Store the user in the repository."""
        with self.lock:
            if self.get_by_email(user.email):
                raise EmailAlreadyRegisteredError()
            self.db.append(user)

    def get_by_id(self, user_id: UserId) -> User | None:
        """Return the user with the given ID, or None."""
        for user in self.db:
            if user.id == user_id:
                return user
        return None

    def get_by_ids(self, user_ids: list[UserId]) -> list[User]:
        """Return users matching the given IDs."""
        users = []

        for user_id in user_ids:
            user = self.get_by_id(user_id)
            if user is not None:
                users.append(user)

        return users

    def get_by_email(self, email: Email) -> User | None:
        """Return the user with the given email, or None."""
        for user in self.db:
            if user.email.value.casefold() == email.value.casefold():
                return user
        return None

    def has_identity(self, user_id: UserId, issuer: str) -> bool:
        """Return whether the account owns an identity from this issuer."""
        with self.lock:
            return any(
                key[0] == issuer and owner.id == user_id for key, owner in self.identities.items()
            )

    def find_identity(self, issuer: str, subject: str) -> User | None:
        """Load the owner of the issuer and subject pair."""
        with self.lock:
            return self.identities.get((issuer, subject))

    def provision(self, user: User, issuer: str, subject: str) -> None:
        """Create the account and identity together."""
        with self.lock:
            if self.find_identity(issuer, subject) or self.get_by_email(user.email):
                raise IdentityConflict()
            self.db.append(user)
            self.identities[issuer, subject] = user

    def link(self, user: User, issuer: str, subject: str) -> None:
        """Attach the identity only if the account can own it."""
        with self.lock:
            owner = self.find_identity(issuer, subject)
            if owner and owner != user:
                raise IdentityConflict()
            self.identities[issuer, subject] = user

    def rename(self, user: User, name: str) -> None:
        """Persist the validated display name."""
        with self.lock:
            user.display_name = DisplayName(name)
