import pytest
from faker import Faker

from domain.identity.infrastructure.adapters.argon_password_hasher import ArgonPasswordHasher
from domain.identity.infrastructure.adapters.in_memory_identity_repository import (
    InMemoryIdentityRepository,
)
from domain.identity.models.aggregates import User
from domain.identity.models.value_objects import DisplayName, Email, PasswordHash


@pytest.fixture
def repository():
    return InMemoryIdentityRepository()


@pytest.fixture
def seeded_repository():
    return InMemoryIdentityRepository(seed=True)


@pytest.fixture
def faker():
    return Faker()


@pytest.fixture
def hasher():
    return ArgonPasswordHasher()


def test_get_by_id(repository, faker, hasher) -> None:
    user = User.register(
        display_name=DisplayName(faker.name()),
        email=Email(faker.email()),
        password_hash=PasswordHash(hasher.hash(faker.password())),
    )

    repository.add_user(user=user)

    returned = repository.get_by_id(user.id)

    assert returned is not None
    assert returned.id == user.id
