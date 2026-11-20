import pytest

from domain.identity.models.aggregates import User
from domain.identity.models.errors import InvalidDisplayNameError, InvalidEmailError
from domain.identity.models.value_objects import DisplayName, Email, PasswordHash


@pytest.mark.parametrize("name", ["   ", "x" * 51])
def test_invalid_display_name_is_rejected(name: str) -> None:
    with pytest.raises(InvalidDisplayNameError):
        DisplayName(name)


def test_invalid_email_is_rejected() -> None:
    with pytest.raises(InvalidEmailError):
        Email("missing-domain")


def test_changing_email_requires_verification_again() -> None:
    user = User.register(
        Email("first@example.com"), DisplayName("Ada"), PasswordHash("$argon2test")
    )
    assert not user.verified
    user.verify_email()
    assert user.verified
    user.change_email(Email("next@example.com"))
    assert user.email.value == "next@example.com"
    assert not user.verified
