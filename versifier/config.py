from dataclasses import dataclass, field
from typing import List

import tomli


@dataclass
class Config:
    private_packages: List[str] = field(default_factory=list)

    @classmethod
    def from_toml(cls, path: str = "pyproject.toml") -> "Config":
        with open(path) as f:
            config = tomli.loads(f.read())

        for k in ["tool", "versifier"]:
            config = config.get(k) or {}

        return cls(**config)
