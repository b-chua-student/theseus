from dataclasses import dataclass

from domain.identity.infrastructure.adapters.argon_password_hasher import ArgonPasswordHasher
from domain.identity.infrastructure.ports.password_hasher import PasswordHasher
from domain.identity.infrastructure.ports.identity_repository import IdentityRepository
from domain.identity.infrastructure.adapters.in_memory_identity_repository import (
    InMemoryIdentityRepository,
)
from domain.project.infrastructure.ports.project_repository import ProjectRepository
from domain.project.infrastructure.adapters.in_memory_project_repository import (
    InMemoryProjectRepository,
)
from .contexts.identity.module import IdentityModule, build_identity_module
from .contexts.project.module import ProjectModule, build_project_module


@dataclass(frozen=True)
class Container:
    identity: IdentityModule
    project: ProjectModule


def build_container(
    identity_repo: IdentityRepository | None = None,
    hasher: PasswordHasher | None = None,
    project_repo: ProjectRepository | None = None,
) -> Container:
    identity_repo = identity_repo or InMemoryIdentityRepository(seed=True)
    hasher = hasher or ArgonPasswordHasher()
    project_repo = project_repo or InMemoryProjectRepository(seed=True)

    return Container(
        identity=build_identity_module(identity_repo, hasher),
        project=build_project_module(project_repo),
    )
