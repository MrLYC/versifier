import logging
import os
import shutil
from dataclasses import dataclass
from subprocess import check_call
from tempfile import TemporaryDirectory
from typing import Iterable, List, Optional

import toml
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

    def _disable_default_source(self, path: str) -> None:
        with open(path, "r") as f:
            config = toml.load(f)

        try:
            sources = config["tool"]["poetry"]["source"]
        except KeyError:
            return

        for source in sources:
            source["default"] = False

        with open(path, "w") as f:
            toml.dump(config, f)

    def export_requirements(
        self,
        include_dev_requirements: bool = False,
        extra_requirements: Optional[Iterable[str]] = None,
        with_credentials: bool = False,
    ) -> RequirementsFile:
        with TemporaryDirectory() as td:
            requirement_path = os.path.join(td, "requirements.txt")
            pyproject_path = os.path.join(td, "pyproject.toml")
            lock_path = os.path.join(td, "poetry.lock")

            shutil.copy("poetry.lock", lock_path)
            shutil.copy("pyproject.toml", pyproject_path)
            self._disable_default_source(pyproject_path)

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

            if with_credentials:
                commands.append("--with-credentials")

            check_call(commands, cwd=td)
            rf = RequirementsFile.from_file(requirement_path)

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

    def init_if_needed(self) -> None:
        if os.path.exists("poetry.lock"):
            return
        check_call([self.poetry_path, "init"])
