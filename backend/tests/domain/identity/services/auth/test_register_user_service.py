from dataclasses import dataclass

import pytest

from domain.identity.infrastructure.adapters.argon_password_hasher import ArgonPasswordHasher
from domain.identity.infrastructure.adapters.in_memory_identity_repository import (
    InMemoryIdentityRepository,
)
from domain.identity.models.errors import InvalidDisplayNameError, InvalidEmailError
from domain.identity.models.value_objects import Email
from domain.identity.services.auth.errors import EmailAlreadyRegisteredError
from domain.identity.services.auth.register_user import RegisterUserService


@pytest.fixture
def repository():
    return InMemoryIdentityRepository()


@pytest.fixture
def hasher():
    return ArgonPasswordHasher()


@pytest.fixture
def service(repository, hasher):
    return RegisterUserService(repository=repository, hasher=hasher)


@pytest.fixture
def test_user():
    return TestUser()


@dataclass
class TestUser:
    display_name = "Test User"
    email = "user@example.com"
    password = "password"


def test_register_creates_user_in_database(repository, service, test_user) -> None:
    service.execute(
        display_name=test_user.display_name, email=test_user.email, password=test_user.password
    )

    user = repository.get_by_email(Email(test_user.email))

    assert user is not None
    assert user.email.value == test_user.email


def test_invalid_email_raises_error(service, test_user) -> None:
    with pytest.raises(InvalidEmailError):
        service.execute(
            display_name=test_user.display_name, email="Invalid Email", password=test_user.password
        )


def test_blank_display_name_raises_error(service, test_user) -> None:
    with pytest.raises(InvalidDisplayNameError):
        service.execute(display_name="", email=test_user.email, password=test_user.password)


def test_long_display_name_raises_error(service, test_user) -> None:
    long_text = "a" * 51

    with pytest.raises(InvalidDisplayNameError):
        service.execute(display_name=long_text, email=test_user.email, password=test_user.password)


def test_register_existing_email_raises_error(service, test_user) -> None:
    service.execute(
        display_name=test_user.email, email=test_user.email, password=test_user.password
    )

    with pytest.raises(EmailAlreadyRegisteredError):
        service.execute(
            display_name=test_user.email, email=test_user.email, password=test_user.password
        )
