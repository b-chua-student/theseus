from flask import Flask

from api.routes.manuscript import manuscripts_bp
from api.routes.project import projects_bp
from api.routes.revision_history import revision_histories_bp
from api.routes.user import users_bp
from repositories.manuscript.fake_manuscript_repository import (
    FakeManuscriptRepository,
)
from repositories.manuscript.manuscript_repository import ManuscriptRepository
from repositories.project.fake_project_repository import FakeProjectRepository
from repositories.project.project_repository import ProjectRepository
from repositories.revision_history.fake_revision_history_repository import (
    FakeRevisionHistoryRepository,
)
from repositories.revision_history.revision_history_repository import RevisionHistoryRepository
from repositories.user.fake_user_repository import FakeUserRepository
from repositories.user.user_repository import UserRepository
from services.manuscript.create_manuscript import CreateManuscriptService
from services.manuscript.delete_manuscript import DeleteManuscriptService
from services.manuscript.get_all_manuscript import GetAllManuscriptService
from services.manuscript.get_manuscript import GetManuscriptService
from services.manuscript.update_manuscript import UpdateManuscriptService
from services.project.create_project import CreateProjectService
from services.project.delete_project import DeleteProjectService
from services.project.get_all_projects import GetAllProjectsService
from services.project.get_project import GetProjectService
from services.project.update_project import UpdateProjectService
from services.revision_history.add_milestone import AddMilestoneService
from services.revision_history.commit_revision import CommitRevisionService
from services.revision_history.create_branch import CreateBranchService
from services.revision_history.delete_branch import DeleteBranchService
from services.revision_history.delete_history import DeleteHistoryService
from services.revision_history.get_all_histories import GetAllHistoriesService
from services.revision_history.get_history import GetHistoryService
from services.revision_history.initialize_history import InitializeHistoryService
from services.revision_history.merge_branches import MergeBranchesService
from services.revision_history.restore_revision import RestoreRevisionService
from services.user.create_user import CreateUserService
from services.user.delete_user import DeleteUserService
from services.user.get_user import GetUserService
from services.user.update_user import UpdateUserService

from .extensions import limiter


def create_app(
    config: dict | None = None,
    manuscript_repo: ManuscriptRepository | None = None,
    revision_history_repo: RevisionHistoryRepository | None = None,
    project_repo: ProjectRepository | None = None,
    user_repo: UserRepository | None = None,
) -> Flask:
    """Create and configure the Flask application.

    Initializes the rate limiter, registers the manuscripts, projects, and
    users blueprints, and wires up the services into ``app.extensions``.

    Args:
        config: Optional configuration values applied to ``app.config``.
        manuscript_repo: Repository for manuscript persistence. Defaults to a
            seeded ``FakeManuscriptRepository``.
        revision_history_repo: Repository for revision history. Defaults to a
            ``FakeRevisionHistoryRepository``.
        project_repo: Repository for project persistence. Defaults to a
            seeded ``FakeProjectRepository``.
        user_repo: Repository for user persistence. Defaults to a seeded
            ``FakeUserRepository``.

    Returns:
        The configured Flask application instance.
    """
    app = Flask(__name__)
    app.config.update(config or {})
    limiter.init_app(app)

    app.register_blueprint(
        manuscripts_bp,
        url_prefix="/api/users/<user_id>/projects/<project_id>/manuscripts",
    )
    app.register_blueprint(projects_bp, url_prefix="/api/projects")
    app.register_blueprint(revision_histories_bp, url_prefix="/api/revision-histories")
    app.register_blueprint(users_bp, url_prefix="/api/users")

    if manuscript_repo is None:
        manuscript_repo = FakeManuscriptRepository(seed=True)
    if revision_history_repo is None:
        revision_history_repo = FakeRevisionHistoryRepository()
    if project_repo is None:
        project_repo = FakeProjectRepository(seed=True)
    if user_repo is None:
        user_repo = FakeUserRepository(seed=True)

    create_manuscript_service = CreateManuscriptService(repository=manuscript_repo)
    app.extensions["create_manuscript_service"] = create_manuscript_service

    get_all_manuscripts_service = GetAllManuscriptService(repository=manuscript_repo)
    app.extensions["get_all_manuscripts_service"] = get_all_manuscripts_service

    get_manuscript_service = GetManuscriptService(repository=manuscript_repo)
    app.extensions["get_manuscript_service"] = get_manuscript_service

    delete_manuscript_service = DeleteManuscriptService(manuscript_repo)
    app.extensions["delete_manuscript_service"] = delete_manuscript_service

    update_manuscript_service = UpdateManuscriptService(repository=manuscript_repo)
    app.extensions["update_manuscript_service"] = update_manuscript_service

    app.extensions["create_project_service"] = CreateProjectService(repository=project_repo)
    app.extensions["get_all_projects_service"] = GetAllProjectsService(repository=project_repo)
    app.extensions["get_project_service"] = GetProjectService(repository=project_repo)
    app.extensions["update_project_service"] = UpdateProjectService(repository=project_repo)
    app.extensions["delete_project_service"] = DeleteProjectService(repository=project_repo)

    app.extensions["create_user_service"] = CreateUserService(repository=user_repo)
    app.extensions["get_user_service"] = GetUserService(repository=user_repo)
    app.extensions["update_user_service"] = UpdateUserService(repository=user_repo)
    app.extensions["delete_user_service"] = DeleteUserService(repository=user_repo)

    app.extensions["initialize_history_service"] = InitializeHistoryService(
        repository=revision_history_repo
    )
    app.extensions["get_history_service"] = GetHistoryService(repository=revision_history_repo)
    app.extensions["get_all_histories_service"] = GetAllHistoriesService(
        repository=revision_history_repo
    )
    app.extensions["delete_history_service"] = DeleteHistoryService(
        repository=revision_history_repo
    )
    app.extensions["commit_revision_service"] = CommitRevisionService(
        repository=revision_history_repo
    )
    app.extensions["restore_revision_service"] = RestoreRevisionService(
        repository=revision_history_repo
    )
    app.extensions["create_branch_service"] = CreateBranchService(repository=revision_history_repo)
    app.extensions["delete_branch_service"] = DeleteBranchService(repository=revision_history_repo)
    app.extensions["add_milestone_service"] = AddMilestoneService(repository=revision_history_repo)
    app.extensions["merge_branches_service"] = MergeBranchesService(
        repository=revision_history_repo
    )

    return app
