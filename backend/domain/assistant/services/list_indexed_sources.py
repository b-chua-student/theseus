from collections.abc import Callable

from domain.assistant.infrastructure.ports.indexed_document_repository import (
    IndexedDocumentRepository,
)
from domain.assistant.models.value_objects import DocumentRefId, ProjectId


class ListIndexedSourcesService:
    """Lists the library sources of a project that the assistant can search.

    Manuscripts are indexed in the same repository, so documents are intersected with the
    project's active library sources, which excludes manuscripts and removed sources.
    """

    def __init__(
        self,
        repository: IndexedDocumentRepository,
        source_ids: Callable[[ProjectId], list[DocumentRefId]] | None,
    ) -> None:
        """Set the document repository and the reader of the project's active source IDs."""
        self._repository = repository
        self._source_ids = source_ids

    def execute(self, project_id: str) -> list[DocumentRefId]:
        """Return the IDs of the project's searchable library sources.

        Raises:
            InvalidProjectIdError: If ``project_id`` is not a valid UUID.
        """
        project = ProjectId.from_str(project_id)
        if self._source_ids is None:
            return []
        active = set(self._source_ids(project))
        return [
            document.doc_ref_id
            for document in self._repository.list_by_project(project)
            if document.is_searchable and document.doc_ref_id in active
        ]
