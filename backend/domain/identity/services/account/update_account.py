from domain.identity.infrastructure.ports.identity_repository import IdentityRepository


class UpdateAccountService:
    """Use case for updating an account (not yet implemented)."""

    def __init__(self, repository: IdentityRepository) -> None:
        self._repository = repository
