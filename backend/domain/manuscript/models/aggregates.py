from __future__ import annotations

from dataclasses import dataclass, field

from .entities import Section
from .events import ManuscriptSaved
from .value_objects import Heading, ManuscriptId, ManuscriptTitle, ProjectId, SectionId

DEFAULT_THESIS_TEMPLATE = (
    "Abstract",
    "Introduction",
    "Literature Review",
    "Methodology",
    "Results",
    "Discussion",
    "Conclusion",
    "References",
)


@dataclass
class Manuscript:
    """The sections of a document, grouped by project, with a renamable title."""

    id: ManuscriptId
    project_id: ProjectId
    title: ManuscriptTitle
    sections: list[Section] = field(default_factory=list)
    _events: list = field(default_factory=list, init=False, repr=False)

    @classmethod
    def create(cls, project_id: ProjectId, title: ManuscriptTitle, *, template: bool) -> Manuscript:
        """Create a manuscript; if template is set, seed it with the default thesis sections."""
        sections = []

        if template:
            last_id = None

            for index, heading in enumerate(DEFAULT_THESIS_TEMPLATE, start=1):
                section_id = SectionId.new()

                last_id = section_id

                sections.append(
                    Section(
                        id=section_id,
                        parent_id=last_id,
                        heading=Heading(heading),
                        ordinal=index,
                    )
                )

        return cls(id=ManuscriptId.new(), project_id=project_id, title=title, sections=sections)

    def rename(self, new_title: ManuscriptTitle) -> None:
        """Replace the manuscript's title."""
        self.title = new_title

    def get_section_by_heading(self, heading: Heading) -> Section | None:
        """Return the first section with the given heading, or None if none match."""
        for section in self.sections:
            if section.heading == heading:
                return section
        return None

    def append_section(self, parent_id: SectionId | None, heading: Heading) -> None:
        """Add a new section at the end, optionally nested under parent_id."""
        self.sections.append(
            Section(
                id=SectionId.new(),
                parent_id=parent_id,
                heading=heading,
                ordinal=len(self.sections) + 1,
            )
        )

    def remove_section(self, section_id: SectionId) -> None:
        """Remove the section with the given id, if present."""
        for section in self.sections:
            if section.id == section_id:
                self.sections.remove(section)

    def rename_section(self, section_id: SectionId, new_heading: Heading) -> None:
        """Rename the section with the given id, if present."""
        for section in self.sections:
            if section.id == section_id:
                section.rename(new_heading)

    def edit_section_body(self, section_id: SectionId, body: str) -> None:
        """Replace the body of the section with the given id and record a ManuscriptSaved event."""
        for section in self.sections:
            if section.id == section_id:
                section.edit_body(body)
                self._events.append(
                    ManuscriptSaved(
                        manuscript_id=self.id.value,
                        project_id=self.project_id.value,
                        section_id=section_id.value,
                        body=body,
                    )
                )

    def pull_events(self) -> list:
        """Return and clear the events recorded since the last call."""
        events, self._events = self._events, []
        return events

    def replace_sections(self, sections: list[Section]) -> None:
        """Replace all sections with the given list."""
        self.sections = list(sections)
