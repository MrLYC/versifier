import os
import tempfile
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

from versifier.poetry import Poetry, RequirementsFile


class TestRequirementsFile:
    def test_from_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            req_path = Path(td) / "requirements.txt"
            req_path.write_text("requests==2.28.0\nflask>=2.0.0\n")
            rf = RequirementsFile.from_file(str(req_path))
            assert len(rf.requirements) == 2
            assert rf.requirements[0].name == "requests"
            assert rf.requirements[1].name == "flask"

    def test_filter_with_include(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            req_path = Path(td) / "requirements.txt"
            req_path.write_text("requests==2.28.0\nflask>=2.0.0\ndjango==4.0\n")
            rf = RequirementsFile.from_file(str(req_path))
            filtered = rf.filter(include=["requests", "flask"])
            assert len(filtered.requirements) == 2
            names = [r.name for r in filtered.requirements]
            assert "requests" in names
            assert "flask" in names
            assert "django" not in names

    def test_filter_with_exclude(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            req_path = Path(td) / "requirements.txt"
            req_path.write_text("requests==2.28.0\nflask>=2.0.0\ndjango==4.0\n")
            rf = RequirementsFile.from_file(str(req_path))
            filtered = rf.filter(exclude=["django"])
            assert len(filtered.requirements) == 2
            names = [r.name for r in filtered.requirements]
            assert "requests" in names
            assert "flask" in names
            assert "django" not in names

    def test_filter_with_markers(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            req_path = Path(td) / "requirements.txt"
            req_path.write_text('requests==2.28.0; python_version >= "3.8"\n')
            rf = RequirementsFile.from_file(str(req_path))
            filtered = rf.filter(markers=["python_version==3.9"])
            assert len(filtered.requirements) == 1

    def test_filter_with_no_filters(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            req_path = Path(td) / "requirements.txt"
            req_path.write_text("requests==2.28.0\nflask>=2.0.0\n")
            rf = RequirementsFile.from_file(str(req_path))
            filtered = rf.filter()
            assert len(filtered.requirements) == 2

    def test_dump_to(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            req_path = Path(td) / "requirements.txt"
            req_path.write_text("requests==2.28.0\n")
            rf = RequirementsFile.from_file(str(req_path))

            output_path = Path(td) / "output.txt"
            rf.dump_to(str(output_path))
            assert output_path.exists()
            content = output_path.read_text()
            assert "requests" in content


class TestPoetry:
    def test_init(self) -> None:
        poetry = Poetry()
        assert poetry.poetry_path == "poetry"

    def test_init_with_custom_path(self) -> None:
        poetry = Poetry(poetry_path="/custom/poetry")
        assert poetry.poetry_path == "/custom/poetry"

    @patch("versifier.poetry.check_call")
    def test_add_packages(self, mock_check_call: MagicMock) -> None:
        poetry = Poetry()
        poetry.add_packages(["requests", "flask"])
        mock_check_call.assert_called_once()
        args = mock_check_call.call_args[0][0]
        assert "poetry" in args
        assert "add" in args
        assert "--lock" in args
        assert "requests" in args
        assert "flask" in args

    @patch("versifier.poetry.check_call")
    def test_add_packages_dev(self, mock_check_call: MagicMock) -> None:
        poetry = Poetry()
        poetry.add_packages(["pytest"], is_dev=True)
        mock_check_call.assert_called_once()
        args = mock_check_call.call_args[0][0]
        assert "--dev" in args

    @patch("versifier.poetry.check_call")
    def test_add_packages_no_lock(self, mock_check_call: MagicMock) -> None:
        poetry = Poetry()
        poetry.add_packages(["requests"], lock_only=False)
        mock_check_call.assert_called_once()
        args = mock_check_call.call_args[0][0]
        assert "--lock" not in args

    @patch("versifier.poetry.check_call")
    def test_install(self, mock_check_call: MagicMock) -> None:
        poetry = Poetry()
        poetry.install()
        mock_check_call.assert_called_once()
        args = mock_check_call.call_args[0][0]
        assert "poetry" in args
        assert "install" in args

    @patch("versifier.poetry.check_call")
    def test_install_with_dev(self, mock_check_call: MagicMock) -> None:
        poetry = Poetry()
        poetry.install(include_dev_requirements=True)
        mock_check_call.assert_called_once()
        args = mock_check_call.call_args[0][0]
        assert "--dev" in args

    @patch("versifier.poetry.check_call")
    def test_install_with_extras(self, mock_check_call: MagicMock) -> None:
        poetry = Poetry()
        poetry.install(extra_requirements=["extra1", "extra2"])
        mock_check_call.assert_called_once()
        args = mock_check_call.call_args[0][0]
        assert "--extras=extra1" in args
        assert "--extras=extra2" in args

    @patch("versifier.poetry.check_call")
    def test_run_command(self, mock_check_call: MagicMock) -> None:
        poetry = Poetry()
        poetry.run_command(["pip", "install", "requests"])
        mock_check_call.assert_called_once()
        args = mock_check_call.call_args[0][0]
        assert args == ["poetry", "run", "pip", "install", "requests"]

    @patch("versifier.poetry.check_call")
    def test_init_if_needed_when_lock_exists(self, mock_check_call: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as td:
            lock_path = Path(td) / "poetry.lock"
            lock_path.write_text("")
            original_dir = os.getcwd()
            try:
                os.chdir(td)
                poetry = Poetry()
                poetry.init_if_needed()
                mock_check_call.assert_not_called()
            finally:
                os.chdir(original_dir)

    @patch("versifier.poetry.check_call")
    def test_init_if_needed_when_lock_not_exists(self, mock_check_call: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as td:
            original_dir = os.getcwd()
            try:
                os.chdir(td)
                poetry = Poetry()
                poetry.init_if_needed()
                mock_check_call.assert_called_once()
                args = mock_check_call.call_args[0][0]
                assert "poetry" in args
                assert "init" in args
            finally:
                os.chdir(original_dir)

    def test_disable_default_source(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            config_path = Path(td) / "pyproject.toml"
            config_path.write_text(
                """
[tool.poetry]
name = "test"

[[tool.poetry.source]]
name = "pypi"
default = true
"""
            )
            poetry = Poetry()
            poetry._disable_default_source(str(config_path))

            import toml

            with open(config_path) as f:
                config = toml.load(f)
            assert config["tool"]["poetry"]["source"][0]["default"] is False

    def test_disable_default_source_no_sources(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            config_path = Path(td) / "pyproject.toml"
            config_path.write_text(
                """
[tool.poetry]
name = "test"
"""
            )
            poetry = Poetry()
            poetry._disable_default_source(str(config_path))

    @patch("versifier.poetry.check_call")
    def test_export_requirements(self, mock_check_call: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as td:
            original_dir = os.getcwd()
            try:
                os.chdir(td)
                Path("poetry.lock").write_text("")
                Path("pyproject.toml").write_text("[tool.poetry]\nname = 'test'\n")

                def side_effect(commands: list, cwd: Optional[str] = None) -> None:
                    req_path = None
                    for cmd in commands:
                        if cmd.startswith("--output="):
                            req_path = cmd.split("=")[1]
                            break
                    if req_path:
                        Path(req_path).write_text("requests==2.28.0\n")

                mock_check_call.side_effect = side_effect

                poetry = Poetry()
                rf = poetry.export_requirements()
                assert rf is not None
            finally:
                os.chdir(original_dir)

    @patch("versifier.poetry.check_call")
    def test_export_requirements_with_options(self, mock_check_call: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as td:
            original_dir = os.getcwd()
            try:
                os.chdir(td)
                Path("poetry.lock").write_text("")
                Path("pyproject.toml").write_text("[tool.poetry]\nname = 'test'\n")

                def side_effect(commands: list, cwd: Optional[str] = None) -> None:
                    req_path = None
                    for cmd in commands:
                        if cmd.startswith("--output="):
                            req_path = cmd.split("=")[1]
                            break
                    if req_path:
                        Path(req_path).write_text("requests==2.28.0\n")

                mock_check_call.side_effect = side_effect

                poetry = Poetry()
                rf = poetry.export_requirements(
                    include_dev_requirements=True, extra_requirements=["extra1"], with_credentials=True
                )
                assert rf is not None
                args = mock_check_call.call_args[0][0]
                assert "--dev" in args
                assert "--extras=extra1" in args
                assert "--with-credentials" in args
            finally:
                os.chdir(original_dir)
