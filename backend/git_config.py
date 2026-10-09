import pathlib
from dulwich.repo import Repo
from dulwich.errors import NotGitRepository

path = pathlib.Path("Repository")
path.mkdir(exist_ok=True)
try:
    repo = Repo(path)
except NotGitRepository:
    repo = Repo.init(path)
