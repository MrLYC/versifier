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
        package_name: str,
    ) -> None:
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

    def compile_all_packages(
        self,
        source_dir: str,
        output_dir: str,
        packages: Optional[Iterable[str]] = None,
    ) -> Iterable[str]:
        packages = packages or os.listdir(source_dir)
        collected_packages = []

        for package in packages:
            package_path = os.path.join(source_dir, package)
            if os.path.isdir(package_path):
                self.compile_package(output_dir, package_path, package)
                collected_packages.append(package_path)
                continue

            package_file_path = f"{package_path}.py"
            if os.path.isfile(package_file_path):
                self.compile_package(output_dir, package_file_path, package)
                collected_packages.append(package_file_path)

        return collected_packages
