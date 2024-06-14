import logging
import os
from dataclasses import dataclass
from subprocess import check_call
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any, Iterable, List

from requirements import parse as parse_requirements

if TYPE_CHECKING:
    from requirements.requirement import Requirement

logger = logging.getLogger(__name__)


@dataclass
class Poetry:
    poetry_path: str

    def _requirement_to_literal(self, r: "Requirement", include_specifier: bool = True, raw: bool = False) -> str:
        if raw:
            return r.line  # type: ignore

        if include_specifier and r.specs:
            specifier = ",".join(f"{i[0]}{i[1]}" for i in r.specs)
        else:
            specifier = ""

        return f"{r.name}{specifier}"

    def _iter_requirements(self, requirements: List[str]) -> Iterable[str]:
        for n in requirements:
            with open(n, "r") as f:
                for r in parse_requirements(f):
                    yield self._requirement_to_literal(r)

    def add_from_requirements_txt(
        self,
        requirements: List[str],
        dev_requirements: List[str],
        exclude: Iterable[str] = (),
        callback: Any = check_call,
    ) -> None:
        exclude_packages = set(exclude)

        commands = [self.poetry_path, "add"]

        requirements_to_add = list(r for r in self._iter_requirements(requirements) if r not in exclude_packages)

        if requirements_to_add:
            logger.info("Adding requirements: %s", requirements_to_add)
            callback(commands + requirements_to_add)

        dev_requirements_to_add = list(
            r for r in self._iter_requirements(dev_requirements) if r not in exclude_packages
        )

        if dev_requirements_to_add:
            logger.info("Adding dev requirements: %s", dev_requirements_to_add)
            callback(commands + ["--dev"] + requirements_to_add)

    def _export_to_requirements_txt_raw(
        self,
        requirements_path: str,
        include_dev_requirements: bool = False,
        extra_requirements: Iterable[str] = (),
    ) -> None:
        commands = [
            self.poetry_path,
            "export",
            "--format=requirements.txt",
            "--without-hashes",
            f"--output={requirements_path}",
        ]

        if include_dev_requirements:
            commands.append("--dev")

        for r in extra_requirements:
            commands.append(f"--extras={r}")

        check_call(commands)

    def export_to_requirements_txt(
        self,
        include_specifiers: bool = True,
        include_comments: bool = False,
        include_dev_requirements: bool = False,
        extra_requirements: Iterable[str] = (),
        exclude: Iterable[str] = (),
        callback: Any = print,
    ) -> None:
        exclude_packages = set(exclude)

        with TemporaryDirectory() as td:
            requirements_path = os.path.join(td, "requirements.txt")

            self._export_to_requirements_txt_raw(
                requirements_path,
                include_dev_requirements=include_dev_requirements,
                extra_requirements=extra_requirements,
            )

            with open(requirements_path, "r") as f:
                for r in parse_requirements(f):
                    if r.name in exclude_packages:
                        continue

                    line = self._requirement_to_literal(r, include_specifier=include_specifiers, raw=include_comments)
                    callback(line)
