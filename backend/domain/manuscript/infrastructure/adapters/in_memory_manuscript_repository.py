from faker import Faker

from domain.manuscript.infrastructure.ports.manuscript_repository import ManuscriptRepository
from domain.manuscript.models.aggregates import Manuscript
from domain.manuscript.models.value_objects import (
    ManuscriptId,
    ManuscriptTitle,
    ProjectId,
)

FAKE_THESIS_TITLES = [
    "Design and Development of an Online Enrollment System",
    "Student Information Management System",
    "Automated Attendance Monitoring System",
    "Web-Based Library Management System",
    "Inventory Management System Using QR Codes",
    "Online Thesis Repository System",
    "Development of a School Management Information System",
    "Cloud-Based Document Management System",
    "AI-Powered Student Performance Prediction",
    "Online Examination and Assessment System",
    "Facial Recognition-Based Attendance System",
    "Barangay Information Management System",
    "E-Commerce Platform for Local Businesses",
    "Secure File Sharing System Using Encryption",
    "Mobile-Based Learning Management System",
]


class InMemoryManuscriptRepository(ManuscriptRepository):
    """List-backed manuscript repository for tests and local development."""

    def __init__(self, *, seed: bool = False, totalManuscripts: int = 5, template: bool) -> None:
        self.db: list[Manuscript] = []
        self.fake = Faker()
        if seed:
            self.seed(totalManuscripts=totalManuscripts, template=template)

    def seed(self, totalManuscripts: int, *, template: bool) -> None:
        project_id = ProjectId.new()

        for _i in range(totalManuscripts):
            self.db.append(
                Manuscript.create(
                    project_id=project_id,
                    title=ManuscriptTitle(self.fake.random_element(FAKE_THESIS_TITLES)),
                    template=template,
                )
            )

        constant_manuscript = Manuscript.create(
            project_id=project_id,
            title=ManuscriptTitle("Test Manuscript"),
            template=template,
        )

        self.db.append(constant_manuscript)

    def save(self, manuscript: Manuscript) -> None:
        for i, existing in enumerate(self.db):
            if existing.id == manuscript.id:
                self.db[i] = manuscript
                return
        self.db.append(manuscript)

    def get_by_id(self, manuscript_id: ManuscriptId) -> Manuscript | None:
        for manuscript in self.db:
            if manuscript.id == manuscript_id:
                return manuscript
        return None

    def list_by_project_id(self, project_id: ProjectId) -> list[Manuscript]:
        manuscripts = []

        for manuscript in self.db:
            if manuscript.project_id == project_id:
                manuscripts.append(manuscript)

        return manuscripts

    def delete(self, manuscript_id: ManuscriptId) -> None:
        self.db = [m for m in self.db if m.id != manuscript_id]

    def get_all(self) -> list[Manuscript]:
        return list(self.db)

    def exists(self, manuscript_id: ManuscriptId) -> bool:
        return any(m.id == manuscript_id for m in self.db)

    def clear(self) -> None:
        self.db.clear()
