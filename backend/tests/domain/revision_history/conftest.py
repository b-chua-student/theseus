import pytest

from bootstrap.contexts.revision_history.module import (
    RevisionHistoryModule,
    build_revision_history_module,
)
from domain.manuscript.infrastructure.adapters.in_memory_manuscript_repository import (
    InMemoryManuscriptRepository,
)
from domain.revision_history.infrastructure.adapters.in_memory_revision_history_repository import (
    InMemoryRevisionHistoryRepository,
)
from domain.revision_history.infrastructure.adapters.manuscript_repository_reader import (
    ManuscriptRepositoryReader,
)
from domain.revision_history.infrastructure.adapters.manuscript_repository_writer import (
    ManuscriptRepositoryWriter,
)
from domain.src_lib.infrastructure.adapters.in_process_event_bus import InProcessEventBus


@pytest.fixture
def manuscript_repository() -> InMemoryManuscriptRepository:
    return InMemoryManuscriptRepository(template=False)


@pytest.fixture
def publisher() -> InProcessEventBus:
    return InProcessEventBus()


@pytest.fixture
def history_repository() -> InMemoryRevisionHistoryRepository:
    return InMemoryRevisionHistoryRepository()


@pytest.fixture
def history_services(
    manuscript_repository: InMemoryManuscriptRepository,
    publisher: InProcessEventBus,
    history_repository: InMemoryRevisionHistoryRepository,
) -> RevisionHistoryModule:
    return build_revision_history_module(
        history_repository,
        ManuscriptRepositoryReader(manuscript_repository),
        ManuscriptRepositoryWriter(manuscript_repository, publisher),
    )
