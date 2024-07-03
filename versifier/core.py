import fnmatch
import logging
import os
import shutil
from dataclasses import dataclass
from itertools import chain
from tempfile import TemporaryDirectory
from typing import Any, Iterable, List, Optional, Set

from .compiler import Compiler
from .poetry import Poetry, RequirementsFile

logger = logging.getLogger(__name__)


@dataclass
class DependencyManager:
    poetry: Poetry

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


@dataclass
class DependencyExporter:
    poetry: Poetry

    def export_to_requirements_txt(
        self,
        include_specifiers: bool = True,
        include_comments: bool = False,
        include_dev_requirements: bool = False,
        with_credentials: bool = False,
        extra_requirements: Iterable[str] = (),
        exclude: Iterable[str] = (),
        markers: Iterable[str] = (),
        callback: Any = print,
    ) -> None:
        rf = self.poetry.export_requirements(
            extra_requirements=extra_requirements,
            include_dev_requirements=include_dev_requirements,
            with_credentials=with_credentials,
        ).filter(exclude=exclude, markers=markers)

        for r in rf.requirements:
            if include_comments:
                callback(r.line)

            elif include_specifiers:
                callback(str(r.req))

            else:
                callback(r.req.name)


@dataclass
class PackageExtractor:
    poetry: Poetry

    def _do_clean_directory(self, path: str, exclude_file_patterns: Iterable[str]) -> None:
        for root, dirs, files in os.walk(path):
            for p in chain(dirs, files):
                filepath = os.path.join(root, p)

                if not os.path.exists(filepath):
                    continue

                for pattern in exclude_file_patterns:
                    if fnmatch.fnmatch(filepath, pattern):
                        shutil.rmtree(filepath)
                        break

    def extract_packages(
        self,
        output_dir: str,
        packages: Iterable[str] = (),
        extra_requirements: Iterable[str] = (),
        exclude_file_patterns: Iterable[str] = (),
    ) -> None:
        exclude_file_patterns = exclude_file_patterns or ("*/*.dist-info", "*/__pycache__")

        rf = self.poetry.export_requirements(
            extra_requirements=extra_requirements,
            include_dev_requirements=True,
            with_credentials=True,
        ).filter(include=packages)

        with TemporaryDirectory() as td:
            requirements_path = os.path.join(td, "requirements.txt")
            rf.dump_to(requirements_path)
            package_path = os.path.join(td, "packages")
            self.poetry.run_command(
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

            self._do_clean_directory(package_path, exclude_file_patterns)
            os.makedirs(output_dir, exist_ok=True)
            for n in os.listdir(package_path):
                os.rename(os.path.join(package_path, n), os.path.join(output_dir, n))


@dataclass
class PackageObfuscator:
    compiler: Compiler

    def obfuscate_packages(
        self,
        packages: Iterable[str],
        root_dir: str,
        output_dir: Optional[str] = None,
        exclude_packages: Optional[List[str]] = None,
    ) -> None:
        in_replace = False

        if output_dir is None:
            output_dir = root_dir
            in_replace = True

        package_set = set()
        for package in packages:
            package_set.add(package)
            package_set.add(package.replace("-", "_"))
            package_set.add(package.replace("_", "-"))

        with TemporaryDirectory() as td:
            collected_packages = self.compiler.compile_packages(root_dir, td, package_set)

            self.compiler.generate_package_stubs(root_dir, td, package_set)

            for output in os.listdir(td):
                shutil.move(os.path.join(td, output), os.path.join(output_dir, output))

        if not in_replace:
            return

        for p in collected_packages:
            if os.path.isdir(p):
                shutil.rmtree(p)
            else:
                os.remove(p)
