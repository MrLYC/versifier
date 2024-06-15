from dataclasses import dataclass, field
from typing import List

import tomli


@dataclass
class Config:
    private_packages: List[str] = field(default_factory=list)

    @classmethod
    def from_toml(cls, path: str) -> "Config":
        with open(path) as f:
            content = tomli.loads(f.read())

        return cls(content["tool"]["versifier"])

    @classmethod
    def from_pyproject_toml(cls) -> "Config":
        return cls.from_toml("pyproject.toml")