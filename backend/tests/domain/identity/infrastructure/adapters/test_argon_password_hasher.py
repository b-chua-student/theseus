import pytest

from domain.identity.infrastructure.adapters.argon_password_hasher import ArgonPasswordHasher


@pytest.fixture
def hasher() -> ArgonPasswordHasher:
    return ArgonPasswordHasher(time_cost=1, memory_cost=64, parallelism=1)


def test_hashes_use_independent_salts(hasher: ArgonPasswordHasher) -> None:
    first = hasher.hash("test password")
    second = hasher.hash("test password")

    assert first != second
    assert hasher.verify("test password", first)
    assert hasher.verify("test password", second)


def test_wrong_password_is_rejected(hasher: ArgonPasswordHasher) -> None:
    assert not hasher.verify("incorrect", hasher.hash("correct"))


def test_unrecognized_hash_is_rejected(hasher: ArgonPasswordHasher) -> None:
    assert not hasher.verify("test password", "not a hash")


def test_changed_parameters_require_rehash(hasher: ArgonPasswordHasher) -> None:
    stored = hasher.hash("test password")
    updated = ArgonPasswordHasher(time_cost=2, memory_cost=64, parallelism=1)

    assert not hasher.needs_rehash(stored)
    assert updated.verify("test password", stored)
    assert updated.needs_rehash(stored)
    assert not updated.needs_rehash(updated.hash("test password"))
