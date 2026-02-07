import logging
import os
from dataclasses import dataclass
from subprocess import check_call
from tempfile import TemporaryDirectory
from typing import Iterable, List, Optional

from .poetry import RequirementsFile

logger = logging.getLogger(__name__)


@dataclass
class Uv:
    uv_path: str = "uv"

    def add_packages(self, packages: Iterable[str], is_dev: bool = False, lock_only: bool = True) -> None:
        commands = [self.uv_path, "add"]

        if is_dev:
            commands.append("--dev")

        if lock_only:
            commands.append("--no-sync")

        commands.extend(packages)
        check_call(commands)

    def export_requirements(
        self,
        include_dev_requirements: bool = False,
        extra_requirements: Optional[Iterable[str]] = None,
        with_credentials: bool = False,
    ) -> RequirementsFile:
        if with_credentials:
            logger.warning("uv export does not support embedding credentials; with_credentials will be ignored")

        with TemporaryDirectory() as td:
            requirement_path = os.path.join(td, "requirements.txt")

            commands = [
                self.uv_path,
                "export",
                "--no-hashes",
                f"--output-file={requirement_path}",
            ]

            if not include_dev_requirements:
                commands.append("--no-dev")

            if extra_requirements:
                commands.extend(f"--extra={i}" for i in extra_requirements)

            check_call(commands)
            rf = RequirementsFile.from_file(requirement_path)

        return rf

    def install(
        self, include_dev_requirements: bool = False, extra_requirements: Optional[Iterable[str]] = None
    ) -> None:
        commands = [self.uv_path, "sync"]

        if not include_dev_requirements:
            commands.append("--no-dev")

        if extra_requirements:
            commands.extend(f"--extra={i}" for i in extra_requirements)

        check_call(commands)

    def run_command(self, args: List[str]) -> None:
        commands = [self.uv_path, "run"]
        commands.extend(args)
        check_call(commands)

    def init_if_needed(self) -> None:
        if os.path.exists("uv.lock"):
            return
        check_call([self.uv_path, "lock"])
