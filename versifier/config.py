import sys
from pathlib import Path
from typing import List

import toml


def get_private_packages_from_pyproject(path: str) -> List[str]:
    if not Path(path).exists():
        return []

    with open(path) as f:
        config = toml.loads(f.read())

    try:
        return config["tool"]["versifier"]["private_packages"]  # type: ignore
    except KeyError:
        pass

    try:
        return config["versifier"]["private_packages"]  # type: ignore
    except KeyError:
        return []


def list_all_packages(path: str = ".") -> List[str]:
    root = Path(path)
    packages = set(i.parent.name for i in root.glob("*/*.py"))

    return list(packages)
