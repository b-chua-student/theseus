from .api import UserDTO, IdentityAPI

from domain.identity.models.aggregates import User
from repositories.identity.identity_repository import IdentityRepository

class InMemoryIdentityAPI(IdentityAPI):
    def __init__(self, repository: IdentityRepository) -> None:
        self._repository = repository

    def _to_dto(self, user: User) -> UserDTO:
        return UserDTO(
            id=str(user.id.value),
            display_name=str(user.display_name.value),
            email=str(user.email),
        )

    def get_user(self, user_id: str) -> UserDTO | None:
        user = self._repository.get_by_id(user_id)

        if (user):
            return self._to_dto(user) 

        return None

    def get_users(self, user_ids: list[str]) -> list[UserDTO]:
        users = self._repository.get_by_ids(user_ids)

        dtos = []

        if (users):
            for user in users:
                dtos.append(self._to_dto(user))

        return dtos


