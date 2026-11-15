from datetime import UTC

import pytest

from domain.identity.models.aggregates import User
from domain.identity.models.value_objects import (
    DisplayName,
    Email,
    PasswordHash,
    UserId,
)


@pytest.fixture
def password_hash() -> PasswordHash:
    return PasswordHash("$argon2id$v=19$m=65536,t=3,p=4$salt$hash")


@pytest.fixture
def user(password_hash: PasswordHash) -> User:
    return User.register(
        email=Email("ana@example.com"),
        display_name=DisplayName("Ana"),
        password_hash=password_hash,
    )


class TestRegister:
    def test_starts_unverified(self, user: User) -> None:
        assert user.verified is False

    def test_generates_id(self, user: User) -> None:
        assert isinstance(user.id, UserId)

    def test_ids_are_unique(self, password_hash: PasswordHash) -> None:
        a = User.register(Email("a@example.com"), DisplayName("A"), password_hash)
        b = User.register(Email("b@example.com"), DisplayName("B"), password_hash)
        assert a.id != b.id

    def test_created_at_is_timezone_aware_utc(self, user: User) -> None:
        assert user.created_at.tzinfo is UTC


class TestVerifyEmail:
    def test_marks_verified(self, user: User) -> None:
        user.verify_email()
        assert user.verified is True

    def test_is_idempotent(self, user: User) -> None:
        user.verify_email()
        user.verify_email()
        assert user.verified is True


class TestChangeEmail:
    def test_replaces_email(self, user: User) -> None:
        user.change_email(Email("new@example.com"))
        assert user.email == Email("new@example.com")

    def test_resets_verification(self, user: User) -> None:
        user.verify_email()
        user.change_email(Email("new@example.com"))
        assert user.verified is False


class TestChangePassword:
    def test_replaces_hash(self, user: User) -> None:
        new_hash = PasswordHash("$argon2id$v=19$m=65536,t=3,p=4$other$hash")
        user.change_password(new_hash)
        assert user.password_hash == new_hash

    def test_does_not_change_verification(self, user: User) -> None:
        user.verify_email()
        user.change_password(PasswordHash("$argon2id$v=19$m=65536,t=3,p=4$x$y"))
        assert user.verified is True


class TestSafety:
    def test_repr_hides_password_hash(self, user: User) -> None:
        assert "argon2" not in repr(user)


class TestEquality:
    def test_same_id_is_equal(self, user: User, password_hash: PasswordHash) -> None:
        clone = User(
            id=user.id,
            display_name=DisplayName("Other"),
            email=Email("other@example.com"),
            password_hash=password_hash,
        )
        assert user == clone  # requires eq-by-id on User

    def test_different_id_is_not_equal(self, password_hash: PasswordHash) -> None:
        a = User.register(Email("a@example.com"), DisplayName("A"), password_hash)
        b = User.register(Email("a@example.com"), DisplayName("A"), password_hash)
        assert a != b
