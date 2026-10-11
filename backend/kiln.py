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

    def commit(self, document_name: str, content: str, commit_author_name: str, commit_author_email: str, commit_message: str, branch_name: str = "master") -> None:
        """Commits a document's content directly to a branch.

        Builds the blob, tree and commit objects without an index or working tree,
        then points the branch ref at the new commit. The parent is taken from HEAD,
        or left empty on the first commit.

        Args:
            document_name (str): Filename of the document inside the tree
                (e.g. "document.docx").
            content (str): Full text content of the document.
            commit_author_name (str): Name of the author. Also used as the committer.
            commit_author_email (str): Email of the author. Also used as the committer.
            commit_message (str): Message describing the change.
            branch_name (str): Branch to update. Created if it does not exist.
                Defaults to "master".

        Returns:
            None.
        """

        FILE_MODE = 0o100644

        blob = Blob.from_string(content.encode(encoding="utf-8"))

        tree = Tree()
        tree.add(document_name.encode(encoding="utf-8"), FILE_MODE, blob.id)

        head_commit: Commit | None = None

        try:
            head_commit = self.repo.__getitem__(self.repo.head())
        except KeyError:
            pass

        if head_commit and head_commit.tree == tree.id:
            raise ValueError("Document is unchanged since last commit.")

        commit = Commit()
        commit.tree = tree.id
        author = (f"{commit_author_name} <{commit_author_email}>").encode(encoding="utf-8")
        commit.author = author
        commit.committer = author
        commit.commit_time = commit.author_time = int(time())
        tz = parse_timezone(b'-0200')[0]
        commit.commit_timezone = commit.author_timezone = tz
        commit.encoding = b"UTF-8"
        commit.message = commit_message.encode(encoding="UTF-8")

        if head_commit:
            commit.parents = [head_commit.id]

        object_store = self.repo.object_store
        object_store.add_object(blob)
        object_store.add_object(tree)
        object_store.add_object(commit)

        ref = f"refs/heads/{branch_name}".encode()
        self.repo.refs[ref] = commit.id
