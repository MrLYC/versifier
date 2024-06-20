from typing import List

import tomli


def get_private_packages_from_pyproject(path: str = "pyproject.toml") -> List[str]:
    with open(path) as f:
        config = tomli.loads(f.read())

    try:
        return config["tool"]["versifier"]["private_packages"]  # type: ignore
    except KeyError:
        return []
