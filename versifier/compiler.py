import os
from dataclasses import dataclass
from subprocess import check_call
from typing import Iterable, Optional

from .stub import PackageStubGenerator


@dataclass
class Compiler:
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
    ) -> Iterable[str]:
        targets = {}
        nofollow_import_to_list = list(nofollow_import_to or [])

        def handle_target(package: str, filename: str) -> bool:
            path = os.path.join(source_dir, filename)
            if os.path.exists(path):
                self._compile_package(
                    output_dir=output_dir,
                    package_path=path,
                    nofollow_import_to=nofollow_import_to_list,
                )
                targets[package] = path

                return True
            return False

        for package in packages:
            name = package
            if handle_target(package, name):
                continue

            if handle_target(package, f"{name}.py"):
                continue

        return targets.values()

    def generate_package_stubs(
        self,
        source_dir: str,
        output_dir: str,
        packages: Iterable[str],
    ) -> None:
        generator = PackageStubGenerator(output_dir=output_dir)
        generator.generate(source_dir=source_dir, packages=packages)
