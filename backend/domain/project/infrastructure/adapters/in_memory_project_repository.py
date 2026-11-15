from faker import Faker

from domain.project.infrastructure.ports.project_repository import ProjectRepository
from domain.project.models.aggregates import Project
from domain.project.models.entities import Member
from domain.project.models.value_objects import DisplayName, Email, MemberId, ProjectId, ProjectName

THESIS_TITLES = [
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


class InMemoryProjectRepository(ProjectRepository):
    """Non-persistent ProjectRepository backed by a list, optionally seeded with fake data."""

    def __init__(self, *, seed: bool = False, totalProjects: int = 5) -> None:
        self._db: list[Project] = []
        self._fake = Faker()
        if seed:
            self.seed(totalProjects=totalProjects)

    def seed(self, totalProjects: int) -> None:
        for _i in range(totalProjects):
            self._db.append(
                Project.create(
                    name=ProjectName(self._fake.random_element(elements=THESIS_TITLES)),
                    owner=Member.join(
                        display_name=DisplayName(self._fake.name()),
                        email=Email(self._fake.email()),
                    ),
                )
            )

    def get_projects_owned_by_member_id(self, member_id: MemberId) -> list[Project]:
        projects = []

        for project in self._db:
            if project.owner.id == member_id:
                projects.append(project)

        return projects

    def add_project(self, project: Project) -> None:
        self._db.append(project)

    def get_project_by_id(self, project_id: ProjectId) -> Project | None:
        for project in self._db:
            if project.id == project_id:
                return project
        return None

    def get_project_by_name(self, project_name: ProjectName) -> Project | None:
        for project in self._db:
            if project.name == project_name:
                return project
        return None

    def update_project(self, new_project: Project) -> None:
        for index, project in enumerate(self._db):
            if project.id == new_project.id:
                self._db[index] = new_project
                return

    def delete_project_by_id(self, project_id: ProjectId) -> None:
        self._db = [project for project in self._db if project.id != project_id]
