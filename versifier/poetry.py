import logging
import os
from dataclasses import dataclass
from subprocess import check_call
from tempfile import TemporaryDirectory
from typing import Any, Iterable, List, Optional, Set

from pip_requirements_parser import RequirementsFile

logger = logging.getLogger(__name__)


@dataclass
class Poetry:
    poetry_path: str

    def _iter_requirements(self, requirements: List[str], exclude_packages: Set[str]) -> Iterable[str]:
        for n in requirements:
            requirements_file = RequirementsFile.from_file(n)
            for r in requirements_file.requirements:
                if r.name in exclude_packages:
                    continue
                yield str(r.req)

    def add_from_requirements_txt(
        self,
        requirements: List[str],
        dev_requirements: List[str],
        exclude: Iterable[str] = (),
        callback: Any = check_call,
    ) -> None:
        exclude_packages = set(exclude)

        commands = [self.poetry_path, "add", "--no-interaction"]

        requirements_to_add = list(self._iter_requirements(requirements, exclude_packages))

        if requirements_to_add:
            logger.info("Adding requirements: %s", requirements_to_add)
            callback(commands + requirements_to_add)

        dev_requirements_to_add = list(self._iter_requirements(dev_requirements, exclude_packages))

        if dev_requirements_to_add:
            logger.info("Adding dev requirements: %s", dev_requirements_to_add)
            callback(commands + ["--dev"] + requirements_to_add)

    def _export_to_requirements_txt_raw(
        self,
        requirements_path: str,
        include_dev_requirements: bool = False,
        extra_requirements: Iterable[str] = (),
        whitelist: Optional[Iterable[str]] = None,
    ) -> None:
        commands = [
            self.poetry_path,
            "export",
            "--format=requirements.txt",
            "--without-hashes",
            "--no-interaction",
            f"--output={requirements_path}",
        ]

        if include_dev_requirements:
            commands.append("--dev")

        for r in extra_requirements:
            commands.append(f"--extras={r}")

        check_call(commands)

        if whitelist is None:
            return

        package_set = set(whitelist)
        rf = RequirementsFile.from_file(requirements_path)
        rf.requirements = [r for r in rf.requirements if r.name in package_set]

        with open(requirements_path, "w") as f:
            f.write(rf.dumps())

    def export_to_requirements_txt(
        self,
        include_specifiers: bool = True,
        include_comments: bool = False,
        include_dev_requirements: bool = False,
        extra_requirements: Iterable[str] = (),
        exclude: Iterable[str] = (),
        markers: Iterable[str] = (),
        callback: Any = print,
    ) -> None:
        exclude_packages = set(exclude)
        marker_dict = dict(m.split("==", 1) for m in markers)

        with TemporaryDirectory() as td:
            requirements_path = os.path.join(td, "requirements.txt")

            self._export_to_requirements_txt_raw(
                requirements_path,
                include_dev_requirements=include_dev_requirements,
                extra_requirements=extra_requirements,
            )

            rf = RequirementsFile.from_file(requirements_path)
            for r in rf.requirements:
                if not r.marker.evaluate(marker_dict):
                    continue

                if r.name in exclude_packages:
                    continue

                if include_comments:
                    callback(r.line)

                elif include_specifiers:
                    callback(str(r.req))

                else:
                    callback(r.req.name)

    def extract_packages(
        self,
        output_dir: str,
        packages: Iterable[str] = (),
        extra_requirements: Iterable[str] = (),
    ) -> None:
        with TemporaryDirectory() as td:
            requirements_path = os.path.join(td, "requirements.txt")

            self._export_to_requirements_txt_raw(
                requirements_path,
                include_dev_requirements=True,
                extra_requirements=extra_requirements,
                whitelist=packages,
            )

            package_path = os.path.join(td, "packages")
            check_call(
                [
                    self.poetry_path,
                    "run",
                    "pip",
                    "install",
                    "--no-deps",
                    "--requirement",
                    requirements_path,
                    "--target",
                    package_path,
                ]
            )

            for n in os.listdir(package_path):
                if not n.startswith("_") and not n.endswith(".dist-info"):
                    os.rename(os.path.join(package_path, n), os.path.join(output_dir, n))
