from dataclasses import dataclass

from domain.identity.infrastructure.ports.identity_repository import IdentityRepository
from domain.identity.infrastructure.ports.password_hasher import PasswordHasher
from domain.identity.services.account.create_account import CreateAccountService
from domain.identity.services.account.get_account import GetAccountService
from domain.identity.services.account.update_account import UpdateAccountService
from domain.identity.services.auth.login_user import LoginUserService
from domain.identity.services.auth.register_user import RegisterUserService


@dataclass(frozen=True)
class AuthModule:
    """Authentication use cases: login and registration."""

    login: LoginUserService
    register: RegisterUserService


@dataclass(frozen=True)
class AccountModule:
    """Account management use cases: create, read and update."""

    create_account: CreateAccountService
    get_account: GetAccountService
    update_account: UpdateAccountService


@dataclass(frozen=True)
class IdentityModule:
    """Identity context services, grouped into authentication and account modules."""

    auth: AuthModule
    account: AccountModule


def build_identity_module(repo: IdentityRepository, hasher: PasswordHasher) -> IdentityModule:
    """Wire the identity services around the given repository and password hasher."""
    return IdentityModule(
        auth=AuthModule(
            login=LoginUserService(repository=repo, hasher=hasher),
            register=RegisterUserService(repository=repo, hasher=hasher),
        ),
        account=AccountModule(
            create_account=CreateAccountService(repository=repo),
            get_account=GetAccountService(repository=repo),
            update_account=UpdateAccountService(repository=repo),
        ),
    )
