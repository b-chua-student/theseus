from dulwich.repo import Repo, MemoryRepo
from dulwich.errors import NotGitRepository
from dulwich.objects import Blob, Tree, Commit, parse_timezone

from time import time

from pathlib import Path


class Kiln:
    """This class is a wrapper around Dulwich's low-level API. It strives to be mapped to native git commands."""

    def __init__(self,document_id: str | int | None = None, storage_dir: str = "kiln", *, persistent: bool = True) -> None:
        """Initializes a Kiln repository for a document.

        Opens the document's bare Git repository, or creates it if it does not exist.
        Pass `persistent=False` for a temporary in-memory repository.

        Args:
            document_id (str | int | None): Unique ID of the document. Used as the
                repository directory name. Required unless `persistent=False`.
            storage_dir (str): Parent directory that holds all document repositories.
                Defaults to "kiln".
            **kwargs: Optional keyword arguments.
                persistent (bool): If False, uses an in-memory repository that is
                    lost when the process ends. Defaults to True.

        Raises:
            ValueError: If `document_id` is empty and `persistent` is not False.
        """

        if persistent is False:
            self.repo = MemoryRepo()
            return

        if not document_id:
            raise ValueError("Error: document_id argument is required.")

        repo_path: Path = Path(storage_dir) / str(document_id)

        try:
            self.repo = Repo(str(repo_path))
        except NotGitRepository:
            repo_path.mkdir(parents=True, exist_ok=True)
            self.repo = Repo.init_bare(repo_path)

    # Setup
    def init(self) -> None: pass
    def clone(self) -> None: pass

    # Staging and committing
    def rm(self) -> None: pass
    def mv(self) -> None: pass
    def commit(self) -> None: pass
    def reset(self) -> None: pass

    # Inspect
    def status(self) -> None: pass
    def log(self) -> None: pass
    def diff(self) -> None: pass
    def show(self) -> None: pass
    def ls_files(self) -> None: pass
    def cat_file(self) -> None: pass

    # Branches and tags
    def branch(self) -> None: pass
    def checkout(self) -> None: pass
    def tag(self) -> None: pass
    def merge(self) -> None: pass

    # Remotes
    def remote(self) -> None: pass
    def fetch(self) -> None: pass
    def pull(self) -> None: pass
    def push(self) -> None: pass
