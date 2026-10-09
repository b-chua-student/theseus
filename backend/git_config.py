import pathlib
from dulwich.repo import Repo

path = pathlib.Path("Repository")
path.mkdir(exist_ok=True)
try:
    repo = Repo(path)
except NotGitRepository:
    repo = Repo.init(path)
