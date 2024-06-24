import sys
from pathlib import Path
from typing import List

import tomli


def get_private_packages_from_pyproject(path: str = "pyproject.toml") -> List[str]:
    with open(path) as f:
        config = tomli.loads(f.read())

    try:
        return config["tool"]["versifier"]["private_packages"]  # type: ignore
    except KeyError:
        return []


def get_site_packages_path() -> str:
    for p in sys.path:
        if p.endswith("site-packages"):
            return p

    return ""


def get_available_packages(path: str = ".") -> List[str]:
    root = Path(path)
    path_set = set(str(i.parent) for i in root.glob("*/*.py"))

    return list(path_set)
