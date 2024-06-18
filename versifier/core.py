import logging
import os
from dataclasses import dataclass, field
from subprocess import check_call
from tempfile import TemporaryDirectory
from typing import Any, Iterable, List, Set

from .poetry import Poetry, RequirementsFile

logger = logging.getLogger(__name__)


@dataclass
class PoetryExtension:
    poetry: Poetry = field(default_factory=Poetry)

    def _merge_requirements(self, requirements: List[str], exclude: Iterable[str] = ()) -> Set[str]:
        results: Set[str] = set()

        for req in requirements:
            rf = RequirementsFile.from_file(req).filter(exclude=exclude)

            results.update(str(r.req) for r in rf.requirements)

        return results

    def add_from_requirements_txt(
        self,
        requirements: List[str],
        dev_requirements: List[str],
        exclude: Iterable[str] = (),
    ) -> None:
        exclude_packages = set(exclude)

        requirements_to_add = self._merge_requirements(requirements, exclude_packages)

        if requirements_to_add:
            logger.info("Adding requirements: %s", requirements_to_add)
            self.poetry.add_packages(requirements_to_add)

        dev_requirements_to_add = self._merge_requirements(dev_requirements, exclude_packages)

        if dev_requirements_to_add:
            logger.info("Adding dev requirements: %s", dev_requirements_to_add)
            self.poetry.add_packages(dev_requirements_to_add, is_dev=True)

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
        rf = self.poetry.export_requirements(
            extra_requirements=extra_requirements,
            include_dev_requirements=include_dev_requirements,
        ).filter(exclude=exclude, markers=markers)

        for r in rf.requirements:
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
        rf = self.poetry.export_requirements(
            extra_requirements=extra_requirements,
            include_dev_requirements=True,
        ).filter(include=packages)

        with TemporaryDirectory() as td:
            requirements_path = os.path.join(td, "requirements.txt")
            rf.dump_to(requirements_path)
            package_path = os.path.join(td, "packages")
            check_call(
                [
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
