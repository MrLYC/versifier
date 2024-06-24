import logging
import os
from dataclasses import dataclass
from subprocess import check_call
from tempfile import TemporaryDirectory
from typing import Iterable, List, Optional

import tomli
from pip_requirements_parser import OptionLine, RequirementLine
from pip_requirements_parser import RequirementsFile as BaseRequirementsFile

logger = logging.getLogger(__name__)


class RequirementsFile(BaseRequirementsFile):
    def filter(
        self,
        include: Iterable[str] = (),
        exclude: Iterable[str] = (),
        markers: Iterable[str] = (),
    ) -> "RequirementsFile":
        includes = set(include)
        excludes = set(exclude)
        marker_dict = dict(m.split("==", 1) for m in markers)
        requirements = []
        for r in self.requirements:
            if includes and r.name not in includes:
                continue

            if excludes and r.name in excludes:
                continue

            if marker_dict and not r.marker.evaluate(marker_dict):
                continue

            requirements.append(r)

        return RequirementsFile(
            filename=self.filename,
            requirements=requirements,
            options=self.options,
            invalid_lines=self.invalid_lines,
            comments=self.comments,
        )

    def dump_to(self, filename: str) -> None:
        with open(filename, "w") as f:
            f.write(self.dumps())

    def update_sources(self, path: str = "pyproject.toml") -> None:
        with open(path, "r") as f:
            config = tomli.loads(f.read())

        try:
            sources = config["tool"]["poetry"]["source"]
        except KeyError:
            return

        for source in sources:
            ol = OptionLine(RequirementLine("", 1), {"extra_index_urls": source["url"]})
            self.options.append(ol)

    @classmethod
    def from_file(cls, filename: str) -> "RequirementsFile":
        rf = BaseRequirementsFile.from_file(filename)
        return cls(
            filename=rf.filename,
            requirements=rf.requirements,
            options=rf.options,
            invalid_lines=rf.invalid_lines,
            comments=rf.comments,
        )


@dataclass
class Poetry:
    poetry_path: str = "poetry"

    def add_packages(self, packages: Iterable[str], is_dev: bool = False, lock_only: bool = True) -> None:
        commands = [self.poetry_path, "add", "--no-interaction"]

        if is_dev:
            commands.append("--dev")

        if lock_only:
            commands.append("--lock")

        commands.extend(packages)
        check_call(commands)

    def export_requirements(
        self,
        include_dev_requirements: bool = False,
        extra_requirements: Optional[Iterable[str]] = None,
    ) -> RequirementsFile:
        with TemporaryDirectory() as td:
            requirement_path = os.path.join(td, "requirements.txt")

            commands = [
                self.poetry_path,
                "export",
                "--no-interaction",
                "--format=requirements.txt",
                f"--output={requirement_path}",
            ]
            if include_dev_requirements:
                commands.append("--dev")

            if extra_requirements:
                commands.extend(f"--extras={i}" for i in extra_requirements)

            check_call(commands)
            rf = RequirementsFile.from_file(requirement_path)
            rf.update_sources()

        return rf

    def install(
        self, include_dev_requirements: bool = False, extra_requirements: Optional[Iterable[str]] = None
    ) -> None:
        commands = [self.poetry_path, "install", "--no-interaction"]

        if include_dev_requirements:
            commands.append("--dev")

        if extra_requirements:
            commands.extend(f"--extras={i}" for i in extra_requirements)

        check_call(commands)

    def run_command(self, args: List[str]) -> None:
        commands = [self.poetry_path, "run"]
        commands.extend(args)
        check_call(commands)
