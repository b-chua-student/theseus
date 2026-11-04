from domain.src_lib.infrastructure.ports.source_repository import SourceRepository
from domain.src_lib.models.aggregates import Source
from domain.src_lib.models.value_objects import SourceId


class InMemorySourceRepository(SourceRepository):
    """Non-persistent source repository backed by a dict, for tests."""

    def __init__(self) -> None:
        self._db: dict[SourceId, Source] = {}

    def get(self, source_id: SourceId) -> Source | None:
        return self._db.get(source_id)

    def list_active(self) -> list[Source]:
        return [s for s in self._db.values() if not s.is_removed]

    def save(self, source: Source) -> None:
        self._db[source.id] = source
