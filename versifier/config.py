from dataclasses import InitVar, dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import toml


@dataclass
class Config:
    root_dir: InitVar[str] = "."
    path: InitVar[str] = "pyproject.toml"
    content: Dict[str, Any] = field(init=False)

    def __post_init__(self, root_dir: str, path: str) -> None:
        config_path = Path(root_dir).joinpath(path)
        if not config_path.exists():
            self.config = {}

        with open(path) as f:
            self.config = toml.loads(f.read())

    def _get_item(self, key: str) -> Any:
        try:
            return self.config["tool"]["versifier"][key]
        except KeyError:
            return self.config["versifier"][key]

    def get_private_packages(self) -> List[str]:
        return self._get_item("private_packages")  # type: ignore

    def get_poetry_extras(self) -> List[str]:
        return self._get_item("poetry_extras")  # type: ignore

    def get_projects_dirs(self) -> List[str]:
        return self._get_item("projects_dirs")  # type: ignore
