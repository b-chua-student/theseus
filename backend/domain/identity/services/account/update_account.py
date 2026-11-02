from domain.identity.infrastructure.ports.identity_repository import IdentityRepository


class UpdateAccountService:
    def __init__(self, repository: IdentityRepository) -> None:
        self._repository = repository
