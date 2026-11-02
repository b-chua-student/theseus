from dataclasses import dataclass

from domain.identity.infrastructure.ports.password_hasher import PasswordHasher
from domain.identity.infrastructure.ports.identity_repository import IdentityRepository
from domain.identity.services.auth.login_user import LoginUserService
from domain.identity.services.auth.register_user import RegisterUserService
from domain.identity.services.account.create_account import CreateAccountService
from domain.identity.services.account.get_account import GetAccountService
from domain.identity.services.account.update_account import UpdateAccountService


@dataclass(frozen=True)
class AuthModule:
    login: LoginUserService
    register: RegisterUserService


@dataclass(frozen=True)
class AccountModule:
    create_account: CreateAccountService
    get_account: GetAccountService
    update_account: UpdateAccountService


@dataclass(frozen=True)
class IdentityModule:
    auth: AuthModule
    account: AccountModule


def build_identity_module(repo: IdentityRepository, hasher: PasswordHasher) -> IdentityModule:
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
