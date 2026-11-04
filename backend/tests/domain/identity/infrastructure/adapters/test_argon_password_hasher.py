import pytest

from domain.identity.infrastructure.adapters.argon_password_hasher import ArgonPasswordHasher


@pytest.fixture
def hasher():
    return ArgonPasswordHasher()


def test_hash_password(hasher) -> None:
    plain = "password"

    hashed = hasher.hash(plain=plain)

    assert hasher.verify(plain, hashed)
