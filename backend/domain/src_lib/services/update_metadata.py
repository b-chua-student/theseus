from domain.src_lib.infrastructure.ports.source_repository import SourceRepository
from domain.src_lib.models.value_objects import Author, SourceId, SourceTitle
from domain.src_lib.services.errors import SourceNotFound


class UpdateMetadataService:
    """Use case: replace a source's title, authors and year."""

    def __init__(self, repository: SourceRepository) -> None:
        self._repository = repository

    def execute(
        self,
        source_id: str,
        title: str,
        authors: list[str],
        year: int | None,
    ) -> None:
        """Update the source's metadata.

        Raises:
            SourceNotFound: if the source does not exist.
        """
        source = self._repository.get(SourceId.from_str(source_id))
        if source is None:
            raise SourceNotFound(source_id)

        source.update_metadata(
            title=SourceTitle(title),
            authors=[Author(a) for a in authors],
            year=year,
        )
        self._repository.save(source)
