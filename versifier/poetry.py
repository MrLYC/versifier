import logging
from subprocess import check_call
from typing import Any, Iterable, List

from requirements import parse as parse_requirements

logger = logging.getLogger(__name__)


def iter_requirements(requirements: List[str]) -> Iterable[str]:
    for n in requirements:
        with open(n, "r") as f:
            for r in parse_requirements(f):
                if not r.specs:
                    yield r.name
                else:
                    specifier = ",".join(f"{i[0]}{i[1]}" for i in r.specs)
                    yield f"{r.name}{specifier}"


def add_from_requirements_txt(
    poetry_path: str,
    requirements: List[str],
    dev_requirements: List[str],
    callback: Any = check_call,
) -> None:
    commands = [poetry_path, "add"]

    requirements_to_add = list(iter_requirements(requirements))

    if requirements_to_add:
        logger.info("Adding requirements: %s", requirements_to_add)
        callback(commands + requirements_to_add)

    dev_requirements_to_add = list(iter_requirements(dev_requirements))

    if dev_requirements_to_add:
        logger.info("Adding dev requirements: %s", dev_requirements_to_add)
        callback(commands + ["--dev"] + requirements_to_add)
