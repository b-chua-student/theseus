import pytest

from domain.identity.infrastructure.adapters.argon_password_hasher import ArgonPasswordHasher
from domain.identity.infrastructure.adapters.in_memory_identity_repository import (
    InMemoryIdentityRepository,
)
from domain.identity.services.accounts.get_account import GetAccountService
from domain.identity.services.auth.errors import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    WeakPasswordError,
)
from domain.identity.services.auth.login_user import LoginUserService
from domain.identity.services.auth.register_user import RegisterUserService

pytestmark = pytest.mark.integration


def test_registered_account_can_sign_in_and_be_retrieved() -> None:
    repo = InMemoryIdentityRepository()
    hasher = ArgonPasswordHasher(time_cost=1, memory_cost=64, parallelism=1)
    register = RegisterUserService(repo, hasher)
    login = LoginUserService(repo, hasher)
    email = "ada@example.com"
    with pytest.raises(WeakPasswordError):
        register.execute("Ada", email, "short")
    user = register.execute(" Ada ", "ada@EXAMPLE.COM", "test password")
    assert user.display_name.value == "Ada"
    with pytest.raises(EmailAlreadyRegisteredError):
        register.execute("Other", email, "another password")
    for address, password in [(email, "wrong"), ("other@example.com", "test password")]:
        with pytest.raises(InvalidCredentialsError, match="^Invalid credentials$"):
            login.execute(address, password)
    authenticated = login.execute(email, "test password")
    assert authenticated.id == user.id
    assert GetAccountService(repo).execute(str(user.id.value)) == user
