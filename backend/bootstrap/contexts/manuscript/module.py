from dataclasses import dataclass

from domain.manuscript.infrastructure.ports.manuscript_repository import ManuscriptRepository
from domain.manuscript.services.append_section import AppendSectionService
from domain.manuscript.services.create_manuscript import CreateManuscriptService
from domain.manuscript.services.delete_manuscript import DeleteManuscriptService
from domain.manuscript.services.edit_section_body import EditSectionBodyService
from domain.manuscript.services.get_manuscript import GetManuscriptService
from domain.manuscript.services.list_manuscripts import ListManuscriptsService
from domain.manuscript.services.remove_section import RemoveSectionService
from domain.manuscript.services.rename_manuscript import RenameManuscriptService
from domain.manuscript.services.rename_section import RenameSectionService
from domain.src_lib.infrastructure.ports.event_publisher import EventPublisher


@dataclass(frozen=True)
class ManuscriptModule:
    """Bundle of manuscript use-case services exposed to the application container."""

    create: CreateManuscriptService
    get: GetManuscriptService
    list: ListManuscriptsService
    delete: DeleteManuscriptService
    rename: RenameManuscriptService
    append_section: AppendSectionService
    remove_section: RemoveSectionService
    rename_section: RenameSectionService
    edit_section_body: EditSectionBodyService


def build_manuscript_module(
    repo: ManuscriptRepository, publisher: EventPublisher
) -> ManuscriptModule:
    """Wire the manuscript services against a repository and event publisher."""
    return ManuscriptModule(
        create=CreateManuscriptService(repository=repo),
        get=GetManuscriptService(repository=repo),
        list=ListManuscriptsService(repository=repo),
        delete=DeleteManuscriptService(repository=repo),
        rename=RenameManuscriptService(repository=repo),
        append_section=AppendSectionService(repository=repo),
        remove_section=RemoveSectionService(repository=repo),
        rename_section=RenameSectionService(repository=repo),
        edit_section_body=EditSectionBodyService(repository=repo, publisher=publisher),
    )
