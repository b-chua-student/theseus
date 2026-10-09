import pathlib
from dulwich.repo import Repo

path = pathlib.Path("Repository")
path.mkdir(exist_ok=True)
repo = Repo.init(path)
