from domain.identity.infrastructure.ports.identity_repository import IdentityRepository


class CreateAccountService:
    def __init__(self, repository: IdentityRepository) -> None:
        self._repository = repository
