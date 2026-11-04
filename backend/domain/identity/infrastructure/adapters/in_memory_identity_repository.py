from faker import Faker

from domain.identity.infrastructure.adapters.argon_password_hasher import ArgonPasswordHasher
from domain.identity.infrastructure.ports.identity_repository import IdentityRepository
from domain.identity.models.aggregates import User, UserId
from domain.identity.models.value_objects import DisplayName, Email, PasswordHash


class InMemoryIdentityRepository(IdentityRepository):
    """Identity repository that keeps users in a list, optionally seeded with fake users."""

    def __init__(self, *, seed: bool = False, totalUsers: int = 5) -> None:
        self.db: list[User] = []
        self.fake = Faker()
        self.hasher = ArgonPasswordHasher()
        if seed:
            self.seed(totalUsers=totalUsers)

    def seed(self, totalUsers: int) -> None:
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
        self.db.append(user)

    def get_by_id(self, user_id: UserId) -> User | None:
        for user in self.db:
            if user.id == user_id:
                return user
        return None

    def get_by_ids(self, user_ids: list[UserId]) -> list[User]:
        users = []

        for user_id in user_ids:
            user = self.get_by_id(user_id)
            if user is not None:
                users.append(user)

        return users

    def get_by_email(self, email: Email) -> User | None:
        for user in self.db:
            if user.email == email:
                return user
        return None
