import os
from dataclasses import dataclass
from subprocess import check_call
from typing import Iterable, Optional


@dataclass
class Compiler:
    nuitka_path: str = "nuitka3"

    def compile_package(
        self,
        output_dir: str,
        package_path: str,
    ) -> None:
        package_name = os.path.basename(package_path)

        check_call(
            [
                self.nuitka_path,
                f"--output-dir={output_dir}",
                "--module",
                package_path,
                f"--include-package={package_name}",
                "--remove-output",
            ]
        )

    def compile_packages(
        self,
        source_dir: str,
        output_dir: str,
        packages: Optional[Iterable[str]] = None,
    ) -> Iterable[str]:
        targets = {}

        def handle_target(package: str, filename: str) -> bool:
            path = os.path.join(source_dir, filename)
            if os.path.exists(path):
                self.compile_package(output_dir, path)
                targets[package] = path

                return True
            return False

        for package in packages or os.listdir(source_dir):
            name = package
            if handle_target(package, name):
                continue

            if handle_target(package, f"{name}.py"):
                continue

            name = package.replace("-", "_")
            if handle_target(package, name):
                continue

            if handle_target(package, f"{name}.py"):
                continue

        return targets.values()
