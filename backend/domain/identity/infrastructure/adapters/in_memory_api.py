from domain.identity.infrastructure.ports.api import IdentityAPI, UserDTO
from domain.identity.infrastructure.ports.identity_repository import IdentityRepository
from domain.identity.models.aggregates import User
from domain.identity.models.value_objects import UserId


class InMemoryIdentityAPI(IdentityAPI):
    """In-memory IdentityAPI that reads users from an identity repository."""

    def __init__(self, repository: IdentityRepository) -> None:
        self._repository = repository

    def _to_dto(self, user: User) -> UserDTO:
        return UserDTO(
            id=str(user.id.value),
            display_name=str(user.display_name.value),
            email=str(user.email),
        )

    def get_user(self, user_id: str) -> UserDTO | None:
        try:
            user = self._repository.get_by_id(UserId.from_str(user_id))
        except ValueError:
            return None

        if user:
            return self._to_dto(user)

        return None

    def get_users(self, user_ids: list[str]) -> list[UserDTO]:
        ids: list[UserId] = []
        for user_id in user_ids:
            try:
                ids.append(UserId.from_str(user_id))
            except ValueError:
                continue

        return [self._to_dto(user) for user in self._repository.get_by_ids(ids)]
