from dataclasses import dataclass
from subprocess import check_call


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
