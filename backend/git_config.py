import pathlib
from dulwich.repo import Repo
from dulwich.errors import NotGitRepository
import os
from dotenv import load_dotenv

load_dotenv()

repo_dir = os.getenv("GIT_REPO_DIR")
if not repo_dir:
    raise ValueError(f"GIT_REPO_DIR must be a non-empty string.")

path = pathlib.Path(repo_dir)
path.mkdir(exist_ok=True)
try:
    repo = Repo(path)
except NotGitRepository:
    repo = Repo.init(path)
