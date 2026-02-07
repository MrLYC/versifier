import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from versifier.__main__ import (
    Context,
    cli,
)


class TestContext:
    def test_context_init(self) -> None:
        ctx = Context(
            root_path="/root",
            config_path="pyproject.toml",
            poetry_path="poetry",
            uv_path="uv",
            nuitka_path="nuitka3",
        )
        assert ctx.root_path == "/root"
        assert ctx.config_path == "pyproject.toml"
        assert ctx.poetry_path == "poetry"
        assert ctx.uv_path == "uv"
        assert ctx.nuitka_path == "nuitka3"

    def test_context_poetry_property(self) -> None:
        ctx = Context(
            root_path="/root",
            config_path="pyproject.toml",
            poetry_path="/custom/poetry",
            uv_path="uv",
            nuitka_path="nuitka3",
        )
        poetry = ctx.poetry
        assert poetry.poetry_path == "/custom/poetry"

    def test_context_compiler_property(self) -> None:
        ctx = Context(
            root_path="/root",
            config_path="pyproject.toml",
            poetry_path="poetry",
            uv_path="uv",
            nuitka_path="/custom/nuitka3",
        )
        compiler = ctx.compiler
        assert compiler is not None

    def test_context_config_property(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            config_path = Path(td) / "pyproject.toml"
            config_path.write_text("[tool.versifier]\nprivate_packages = ['pkg1']\n")

            original_dir = os.getcwd()
            try:
                os.chdir(td)
                ctx = Context(
                    root_path=td,
                    config_path="pyproject.toml",
                    poetry_path="poetry",
                    uv_path="uv",
                    nuitka_path="nuitka3",
                )
                config = ctx.config
                assert config.get_private_packages() == ["pkg1"]
            finally:
                os.chdir(original_dir)

    def test_context_root_dir_property(self) -> None:
        ctx = Context(
            root_path="/root/path",
            config_path="pyproject.toml",
            poetry_path="poetry",
            uv_path="uv",
            nuitka_path="nuitka3",
        )
        assert ctx.root_dir == Path("/root/path")

    def test_context_uv_property(self) -> None:
        ctx = Context(
            root_path="/root",
            config_path="pyproject.toml",
            poetry_path="poetry",
            uv_path="/custom/uv",
            nuitka_path="nuitka3",
        )
        uv = ctx.uv
        assert uv.uv_path == "/custom/uv"

    def test_context_package_manager_uv(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            Path(td, "uv.lock").write_text("")
            original_dir = os.getcwd()
            try:
                os.chdir(td)
                ctx = Context(
                    root_path=td,
                    config_path="pyproject.toml",
                    poetry_path="poetry",
                    uv_path="uv",
                    nuitka_path="nuitka3",
                )
                from versifier.uv import Uv

                assert isinstance(ctx.package_manager, Uv)
            finally:
                os.chdir(original_dir)

    def test_context_package_manager_poetry(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            Path(td, "poetry.lock").write_text("")
            original_dir = os.getcwd()
            try:
                os.chdir(td)
                ctx = Context(
                    root_path=td,
                    config_path="pyproject.toml",
                    poetry_path="poetry",
                    uv_path="uv",
                    nuitka_path="nuitka3",
                )
                from versifier.poetry import Poetry

                assert isinstance(ctx.package_manager, Poetry)
            finally:
                os.chdir(original_dir)

    def test_context_package_manager_none(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            original_dir = os.getcwd()
            try:
                os.chdir(td)
                ctx = Context(
                    root_path=td,
                    config_path="pyproject.toml",
                    poetry_path="poetry",
                    uv_path="uv",
                    nuitka_path="nuitka3",
                )
                import pytest

                with pytest.raises(Exception):
                    ctx.package_manager
            finally:
                os.chdir(original_dir)

    def test_context_package_manager_prefers_uv(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            Path(td, "uv.lock").write_text("")
            Path(td, "poetry.lock").write_text("")
            original_dir = os.getcwd()
            try:
                os.chdir(td)
                ctx = Context(
                    root_path=td,
                    config_path="pyproject.toml",
                    poetry_path="poetry",
                    uv_path="uv",
                    nuitka_path="nuitka3",
                )
                from versifier.uv import Uv

                assert isinstance(ctx.package_manager, Uv)
            finally:
                os.chdir(original_dir)

    def test_context_wrapper(self) -> None:
        @Context.wrapper
        def test_func(ctx: Context, extra_arg: str) -> str:
            return f"{ctx.root_path}:{extra_arg}"

        assert hasattr(test_func, "__wrapped__")


class TestCLI:
    def test_cli_group(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "requirements-to-poetry" in result.output
        assert "poetry-to-requirements" in result.output

    @patch("versifier.__main__.core.DependencyManager")
    def test_requirements_to_poetry(self, mock_manager_class: MagicMock) -> None:
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("requirements.txt").write_text("requests==2.28.0\n")
            Path("pyproject.toml").write_text("[tool.poetry]\nname = 'test'\n")
            Path("poetry.lock").write_text("")

            result = runner.invoke(
                cli,
                [
                    "requirements-to-poetry",
                    "-R",
                    "requirements.txt",
                    "--add-only",
                ],
            )

            if result.exit_code != 0:
                print(result.output)
            assert result.exit_code == 0

    @patch("versifier.__main__.core.DependencyManager")
    def test_requirements_to_poetry_init(self, mock_manager_class: MagicMock) -> None:
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("requirements.txt").write_text("requests==2.28.0\n")
            Path("pyproject.toml").write_text("[tool.poetry]\nname = 'test'\n")

            with patch("versifier.__main__.Poetry") as mock_poetry_class:
                mock_poetry = MagicMock()
                mock_poetry_class.return_value = mock_poetry

                runner.invoke(
                    cli,
                    [
                        "requirements-to-poetry",
                        "-R",
                        "requirements.txt",
                    ],
                )

                mock_poetry.init_if_needed.assert_called_once()

    @patch("versifier.__main__.core.DependencyExporter")
    def test_poetry_to_requirements(self, mock_exporter_class: MagicMock) -> None:
        mock_exporter = MagicMock()
        mock_exporter_class.return_value = mock_exporter

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("pyproject.toml").write_text("[tool.poetry]\nname = 'test'\n")

            result = runner.invoke(
                cli,
                [
                    "poetry-to-requirements",
                    "-o",
                    "output.txt",
                ],
            )

            if result.exit_code != 0:
                print(result.output)
            assert result.exit_code == 0

    @patch("versifier.__main__.core.DependencyExporter")
    def test_poetry_to_requirements_stdout(self, mock_exporter_class: MagicMock) -> None:
        mock_exporter = MagicMock()
        mock_exporter_class.return_value = mock_exporter

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("pyproject.toml").write_text("[tool.poetry]\nname = 'test'\n")

            result = runner.invoke(
                cli,
                [
                    "poetry-to-requirements",
                    "-o",
                    "",
                ],
            )

            if result.exit_code != 0:
                print(result.output)
            assert result.exit_code == 0

    @patch("versifier.__main__.core.DependencyExporter")
    def test_poetry_to_requirements_with_private_packages_from_config(
        self, mock_exporter_class: MagicMock
    ) -> None:
        mock_exporter = MagicMock()
        mock_exporter_class.return_value = mock_exporter

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("pyproject.toml").write_text(
                "[tool.poetry]\nname = 'test'\n\n[tool.versifier]\nprivate_packages = ['pkg1']\n"
            )

            result = runner.invoke(
                cli,
                [
                    "poetry-to-requirements",
                    "-o",
                    "output.txt",
                ],
            )

            assert result.exit_code == 0

    @patch("versifier.__main__.core.PackageExtractor")
    def test_extract_private_packages(self, mock_extractor_class: MagicMock) -> None:
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("pyproject.toml").write_text("[tool.poetry]\nname = 'test'\n")
            Path("poetry.lock").write_text("")

            result = runner.invoke(
                cli,
                [
                    "extract-private-packages",
                    "-o",
                    "output",
                    "-P",
                    "pkg1",
                ],
            )

            if result.exit_code != 0:
                print(result.output)
            assert result.exit_code == 0
            mock_extractor.extract_packages.assert_called_once()

    def test_extract_private_packages_no_packages(self) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("pyproject.toml").write_text("[tool.poetry]\nname = 'test'\n")
            Path("poetry.lock").write_text("")

            result = runner.invoke(
                cli,
                [
                    "extract-private-packages",
                    "-o",
                    "output",
                ],
            )

            assert result.exit_code != 0
            assert "No private packages found" in result.output

    @patch("versifier.__main__.core.PackageExtractor")
    def test_extract_private_packages_from_config(self, mock_extractor_class: MagicMock) -> None:
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("pyproject.toml").write_text(
                "[tool.poetry]\nname = 'test'\n\n[tool.versifier]\nprivate_packages = ['pkg1']\n"
            )
            Path("poetry.lock").write_text("")

            result = runner.invoke(
                cli,
                [
                    "extract-private-packages",
                    "-o",
                    "output",
                ],
            )

            assert result.exit_code == 0

    @patch("versifier.__main__.core.PackageObfuscator")
    def test_obfuscate_project_dirs(self, mock_obfuscator_class: MagicMock) -> None:
        mock_obfuscator = MagicMock()
        mock_obfuscator_class.return_value = mock_obfuscator

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("pyproject.toml").write_text("[tool.poetry]\nname = 'test'\n")
            os.makedirs("subdir")
            os.makedirs("subdir/pkg")
            Path("subdir/pkg/__init__.py").write_text("")

            result = runner.invoke(
                cli,
                [
                    "obfuscate-project-dirs",
                    "-o",
                    "output",
                    "-d",
                    "subdir",
                ],
            )

            if result.exit_code != 0:
                print(result.output)
            assert result.exit_code == 0

    @patch("versifier.__main__.core.PackageObfuscator")
    def test_obfuscate_project_dirs_from_config(self, mock_obfuscator_class: MagicMock) -> None:
        mock_obfuscator = MagicMock()
        mock_obfuscator_class.return_value = mock_obfuscator

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("pyproject.toml").write_text(
                "[tool.poetry]\nname = 'test'\n\n[tool.versifier]\nprojects_dirs = ['subdir']\n"
            )
            os.makedirs("subdir")
            os.makedirs("subdir/pkg")
            Path("subdir/pkg/__init__.py").write_text("")

            result = runner.invoke(
                cli,
                [
                    "obfuscate-project-dirs",
                    "-o",
                    "output",
                ],
            )

            assert result.exit_code == 0

    @patch("versifier.__main__.core.PackageObfuscator")
    @patch("versifier.__main__.core.PackageExtractor")
    def test_obfuscate_private_packages(
        self, mock_extractor_class: MagicMock, mock_obfuscator_class: MagicMock
    ) -> None:
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor
        mock_obfuscator = MagicMock()
        mock_obfuscator_class.return_value = mock_obfuscator

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("pyproject.toml").write_text("[tool.poetry]\nname = 'test'\n")
            Path("poetry.lock").write_text("")

            result = runner.invoke(
                cli,
                [
                    "obfuscate-private-packages",
                    "-o",
                    "output",
                    "-P",
                    "pkg1",
                ],
            )

            if result.exit_code != 0:
                print(result.output)
            assert result.exit_code == 0

    def test_obfuscate_private_packages_no_packages(self) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("pyproject.toml").write_text("[tool.poetry]\nname = 'test'\n")
            Path("poetry.lock").write_text("")

            result = runner.invoke(
                cli,
                [
                    "obfuscate-private-packages",
                    "-o",
                    "output",
                ],
            )

            assert result.exit_code != 0
            assert "No private packages found" in result.output

    @patch("versifier.__main__.core.PackageObfuscator")
    @patch("versifier.__main__.core.PackageExtractor")
    def test_obfuscate_private_packages_from_config(
        self, mock_extractor_class: MagicMock, mock_obfuscator_class: MagicMock
    ) -> None:
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor
        mock_obfuscator = MagicMock()
        mock_obfuscator_class.return_value = mock_obfuscator

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("pyproject.toml").write_text(
                "[tool.poetry]\nname = 'test'\n\n[tool.versifier]\nprivate_packages = ['pkg1']\n"
            )
            Path("poetry.lock").write_text("")

            result = runner.invoke(
                cli,
                [
                    "obfuscate-private-packages",
                    "-o",
                    "output",
                ],
            )

            assert result.exit_code == 0

    def test_command_details(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["command-details"])
        assert result.exit_code == 0
        assert "requirements-to-poetry" in result.output
        assert "poetry-to-requirements" in result.output
        assert "requirements-to-uv" in result.output
        assert "uv-to-requirements" in result.output

    @patch("versifier.__main__.core.DependencyManager")
    def test_requirements_to_uv(self, mock_manager_class: MagicMock) -> None:
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("requirements.txt").write_text("requests==2.28.0\n")
            Path("pyproject.toml").write_text("[project]\nname = 'test'\n")
            Path("uv.lock").write_text("")

            result = runner.invoke(
                cli,
                [
                    "requirements-to-uv",
                    "-R",
                    "requirements.txt",
                    "--add-only",
                ],
            )

            if result.exit_code != 0:
                print(result.output)
            assert result.exit_code == 0

    @patch("versifier.__main__.core.DependencyManager")
    def test_requirements_to_uv_init(self, mock_manager_class: MagicMock) -> None:
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("requirements.txt").write_text("requests==2.28.0\n")
            Path("pyproject.toml").write_text("[project]\nname = 'test'\n")

            with patch("versifier.__main__.Uv") as mock_uv_class:
                mock_uv = MagicMock()
                mock_uv_class.return_value = mock_uv

                runner.invoke(
                    cli,
                    [
                        "requirements-to-uv",
                        "-R",
                        "requirements.txt",
                    ],
                )

                mock_uv.init_if_needed.assert_called_once()

    @patch("versifier.__main__.core.DependencyExporter")
    def test_uv_to_requirements(self, mock_exporter_class: MagicMock) -> None:
        mock_exporter = MagicMock()
        mock_exporter_class.return_value = mock_exporter

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("pyproject.toml").write_text("[project]\nname = 'test'\n")

            result = runner.invoke(
                cli,
                [
                    "uv-to-requirements",
                    "-o",
                    "output.txt",
                ],
            )

            if result.exit_code != 0:
                print(result.output)
            assert result.exit_code == 0

    @patch("versifier.__main__.core.DependencyExporter")
    def test_uv_to_requirements_stdout(self, mock_exporter_class: MagicMock) -> None:
        mock_exporter = MagicMock()
        mock_exporter_class.return_value = mock_exporter

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("pyproject.toml").write_text("[project]\nname = 'test'\n")

            result = runner.invoke(
                cli,
                [
                    "uv-to-requirements",
                    "-o",
                    "",
                ],
            )

            if result.exit_code != 0:
                print(result.output)
            assert result.exit_code == 0

    @patch("versifier.__main__.core.DependencyExporter")
    def test_uv_to_requirements_with_private_packages_from_config(
        self, mock_exporter_class: MagicMock
    ) -> None:
        mock_exporter = MagicMock()
        mock_exporter_class.return_value = mock_exporter

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("pyproject.toml").write_text(
                "[project]\nname = 'test'\n\n[tool.versifier]\nprivate_packages = ['pkg1']\n"
            )

            result = runner.invoke(
                cli,
                [
                    "uv-to-requirements",
                    "-o",
                    "output.txt",
                ],
            )

            assert result.exit_code == 0

    @patch("versifier.__main__.core.PackageExtractor")
    def test_extract_private_packages_with_uv(self, mock_extractor_class: MagicMock) -> None:
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("pyproject.toml").write_text("[project]\nname = 'test'\n")
            Path("uv.lock").write_text("")

            result = runner.invoke(
                cli,
                [
                    "extract-private-packages",
                    "-o",
                    "output",
                    "-P",
                    "pkg1",
                ],
            )

            if result.exit_code != 0:
                print(result.output)
            assert result.exit_code == 0
            mock_extractor.extract_packages.assert_called_once()

    @patch("versifier.__main__.core.PackageObfuscator")
    def test_obfuscate_project_dirs_with_uv(self, mock_obfuscator_class: MagicMock) -> None:
        mock_obfuscator = MagicMock()
        mock_obfuscator_class.return_value = mock_obfuscator

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("pyproject.toml").write_text("[project]\nname = 'test'\n")
            Path("uv.lock").write_text("")
            os.makedirs("subdir")
            os.makedirs("subdir/pkg")
            Path("subdir/pkg/__init__.py").write_text("")

            result = runner.invoke(
                cli,
                [
                    "obfuscate-project-dirs",
                    "-o",
                    "output",
                    "-d",
                    "subdir",
                ],
            )

            if result.exit_code != 0:
                print(result.output)
            assert result.exit_code == 0

    @patch("versifier.__main__.core.PackageObfuscator")
    @patch("versifier.__main__.core.PackageExtractor")
    def test_obfuscate_private_packages_with_uv(
        self, mock_extractor_class: MagicMock, mock_obfuscator_class: MagicMock
    ) -> None:
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor
        mock_obfuscator = MagicMock()
        mock_obfuscator_class.return_value = mock_obfuscator

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("pyproject.toml").write_text("[project]\nname = 'test'\n")
            Path("uv.lock").write_text("")

            result = runner.invoke(
                cli,
                [
                    "obfuscate-private-packages",
                    "-o",
                    "output",
                    "-P",
                    "pkg1",
                ],
            )

            if result.exit_code != 0:
                print(result.output)
            assert result.exit_code == 0
