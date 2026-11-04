from repositories.identity.identity_repository import IdentityRepository

from domain.identity.models.aggregates import User

from .api import IdentityAPI, UserDTO


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
        user = self._repository.get_by_id(user_id)

        if user:
            return self._to_dto(user)

        return None

    def get_users(self, user_ids: list[str]) -> list[UserDTO]:
        users = self._repository.get_by_ids(user_ids)

        dtos = []

        if users:
            for user in users:
                dtos.append(self._to_dto(user))

        return dtos
