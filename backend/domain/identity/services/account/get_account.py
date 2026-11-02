from domain.identity.infrastructure.ports.identity_repository import IdentityRepository
from domain.identity.models.aggregates import User
from domain.identity.models.value_objects import UserId


class GetAccountService:
    def __init__(self, repository: IdentityRepository) -> None:
        self._repository = repository

    def execute(self, user_id: str) -> User | None:
        valid_id = UserId.from_str(user_id)
        return self._repository.get_by_id(valid_id)
