from dataclasses import dataclass

from domain.src_lib.infrastructure.ports.event_publisher import EventPublisher
from domain.src_lib.infrastructure.ports.source_repository import SourceRepository
from domain.src_lib.services.add_source import AddSourceService
from domain.src_lib.services.get_source import GetSourceService
from domain.src_lib.services.list_sources import ListSourcesService
from domain.src_lib.services.remove_source import RemoveSourceService
from domain.src_lib.services.update_metadata import UpdateMetadataService


@dataclass(frozen=True)
class SourceModule:
    """Bundle of source library services wired to a shared repository."""

    add: AddSourceService
    get: GetSourceService
    list: ListSourcesService
    remove: RemoveSourceService
    update_metadata: UpdateMetadataService


def build_source_module(repo: SourceRepository, publisher: EventPublisher) -> SourceModule:
    """Construct a SourceModule with services wired to the given adapters."""
    return SourceModule(
        add=AddSourceService(repository=repo, publisher=publisher),
        get=GetSourceService(repository=repo),
        list=ListSourcesService(repository=repo),
        remove=RemoveSourceService(repository=repo, publisher=publisher),
        update_metadata=UpdateMetadataService(repository=repo),
    )
