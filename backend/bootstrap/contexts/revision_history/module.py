from dataclasses import dataclass

from domain.revision_history.infrastructure.ports.manuscript_reader import ManuscriptReader
from domain.revision_history.infrastructure.ports.manuscript_writer import ManuscriptWriter
from domain.revision_history.infrastructure.ports.revision_history_repository import (
    RevisionHistoryRepository,
)
from domain.revision_history.services.commit_revision import CommitRevisionService
from domain.revision_history.services.create_draft import CreateDraftService
from domain.revision_history.services.delete_draft import DeleteDraftService
from domain.revision_history.services.get_current_content import GetCurrentContentService
from domain.revision_history.services.get_draft import GetDraftService
from domain.revision_history.services.get_revision import GetRevisionService
from domain.revision_history.services.list_drafts import ListDraftsService
from domain.revision_history.services.list_revisions import ListRevisionsService
from domain.revision_history.services.rename_draft import RenameDraftService
from domain.revision_history.services.restore_revision import RestoreRevisionService
from domain.revision_history.services.start_revision_history import StartRevisionHistoryService
from domain.revision_history.services.switch_draft import SwitchDraftService


@dataclass(frozen=True)
class RevisionHistoryModule:
    """Bundle of revision history services wired to a shared repository."""

    start: StartRevisionHistoryService
    commit: CommitRevisionService
    list: ListRevisionsService
    get: GetRevisionService
    restore: RestoreRevisionService
    create_draft: CreateDraftService
    list_drafts: ListDraftsService
    get_draft: GetDraftService
    rename_draft: RenameDraftService
    delete_draft: DeleteDraftService
    switch_draft: SwitchDraftService
    current_content: GetCurrentContentService


def build_revision_history_module(
    repo: RevisionHistoryRepository,
    reader: ManuscriptReader,
    writer: ManuscriptWriter,
) -> RevisionHistoryModule:
    """Construct a RevisionHistoryModule with services wired to the given adapters."""
    return RevisionHistoryModule(
        start=StartRevisionHistoryService(repository=repo, reader=reader),
        commit=CommitRevisionService(repository=repo, reader=reader),
        list=ListRevisionsService(repository=repo),
        get=GetRevisionService(repository=repo),
        restore=RestoreRevisionService(repository=repo, writer=writer),
        create_draft=CreateDraftService(repository=repo),
        list_drafts=ListDraftsService(repository=repo),
        get_draft=GetDraftService(repository=repo),
        rename_draft=RenameDraftService(repository=repo),
        delete_draft=DeleteDraftService(repository=repo),
        switch_draft=SwitchDraftService(repository=repo, writer=writer),
        current_content=GetCurrentContentService(repository=repo),
    )
