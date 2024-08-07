import logging
import os
import shutil
from dataclasses import dataclass
from distutils.core import setup
from subprocess import check_call
from tempfile import TemporaryDirectory
from typing import Any, Dict, Iterable, List, Optional

from Cython.Build import cythonize
from typing_extensions import Protocol

logger = logging.getLogger(__name__)


class Compiler(Protocol):
    def compile_packages(
        self, source_dir: str, output_dir: str, packages: Iterable[str], **kwargs: Dict[str, Any]
    ) -> None:
        ...


@dataclass
class Nuitka3:
    nuitka_path: str = "nuitka3"

    def _compile_package(
        self,
        output_dir: str,
        package_path: str,
        nofollow_import_to: Optional[Iterable[str]] = None,
    ) -> None:
        package_dir = os.path.dirname(package_path)
        package_name = os.path.basename(package_path)
        commands = [
            self.nuitka_path,
            f"--output-dir={output_dir}",
            "--module",
            package_name,
            f"--include-package={package_name}",
            "--remove-output",
            "--no-pyi-file",
        ]

        if nofollow_import_to:
            commands.extend(f"--nofollow-import-to={i}" for i in nofollow_import_to)

        check_call(commands, cwd=package_dir)

    def compile_packages(
        self,
        source_dir: str,
        output_dir: str,
        packages: Iterable[str],
        nofollow_import_to: Optional[Iterable[str]] = None,
        **kwargs: Dict[str, Any],
    ) -> None:
        nofollow_import_to_list = list(nofollow_import_to or [])

        def handle_target(package: str, filename: str) -> bool:
            path = os.path.join(source_dir, filename)
            if os.path.exists(path):
                self._compile_package(
                    output_dir=output_dir,
                    package_path=path,
                    nofollow_import_to=nofollow_import_to_list,
                )

                return True
            return False

        for package in packages:
            name = package
            if handle_target(package, name):
                continue

            if handle_target(package, f"{name}.py"):
                continue


class Cython:
    def compile_packages(
        self, source_dir: str, output_dir: str, packages: Iterable[str], **kwargs: Dict[str, Any]
    ) -> None:
        os.makedirs(output_dir, exist_ok=True)
        module_list = []
        with TemporaryDirectory() as td:
            for package in packages:
                package_path = os.path.join(source_dir, package)

                if os.path.isdir(package_path):
                    for root, _, files in os.walk(package_path):
                        for file in files:
                            if file.endswith(".py"):
                                module_list.append(os.path.join(root, file))
                else:
                    package_file = f"{package_path}.py"
                    if not os.path.isfile(package_file):
                        continue

                    target_path = f"{os.path.join(td, package)}.py"
                    shutil.copy(package_file, target_path)
                    module_list.append(target_path)

            cur_dir = os.path.realpath(os.curdir)
            os.chdir(source_dir)
            try:
                setup(
                    ext_modules=cythonize(module_list, compiler_directives={"language_level": 3}, build_dir=td),
                    script_args=["build_ext", "-b", output_dir, "-t", td],
                )
            finally:
                os.chdir(cur_dir)


@dataclass
class SmartCompiler:
    compilers: List[Compiler]

    def compile_packages(
        self,
        source_dir: str,
        output_dir: str,
        packages: Iterable[str],
        **kwargs: Dict[str, Any],
    ) -> None:
        failed_packages = packages

        for compiler in self.compilers:
            packages = failed_packages
            failed_packages = []

            for package in packages:
                try:
                    compiler.compile_packages(source_dir, output_dir, [package], **kwargs)
                except Exception as e:
                    logger.warning("Failed to compile package %s with %s: %s", package, compiler, e)
                    failed_packages.append(package)
