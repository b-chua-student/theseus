from abc import abstractmethod, ABC

from domain.identity.models.value_objects import Email, UserId
from domain.identity.models.aggregates import User

class IdentityRepository(ABC):
    @abstractmethod
    def add_user(self, user: User) -> User | None:
        pass

    @abstractmethod
    def get_by_id(self, user_id: UserId) -> User | None:
        pass

    @abstractmethod
    def get_by_ids(self, user_ids: list[UserId]) -> list[User] | None:
        pass

    @abstractmethod
    def get_by_email(self, email: Email) -> User | None:
        pass
