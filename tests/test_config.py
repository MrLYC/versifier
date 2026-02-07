import tempfile
from pathlib import Path

from versifier.config import Config


class TestConfig:
    def test_config_with_nonexistent_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            config = Config(root_dir=td, path="nonexistent.toml")
            assert config.config == {}

    def test_config_with_tool_versifier_section(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            config_path = Path(td) / "pyproject.toml"
            config_path.write_text(
                """
[tool.versifier]
private_packages = ["pkg1", "pkg2"]
poetry_extras = ["extra1"]
projects_dirs = ["dir1", "dir2"]
"""
            )
            config = Config(root_dir=td, path="pyproject.toml")
            assert config.get_private_packages() == ["pkg1", "pkg2"]
            assert config.get_poetry_extras() == ["extra1"]
            assert config.get_projects_dirs() == ["dir1", "dir2"]

    def test_config_with_versifier_section(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            config_path = Path(td) / "pyproject.toml"
            config_path.write_text(
                """
[versifier]
private_packages = ["pkg3", "pkg4"]
poetry_extras = ["extra2"]
projects_dirs = ["dir3"]
"""
            )
            config = Config(root_dir=td, path="pyproject.toml")
            assert config.get_private_packages() == ["pkg3", "pkg4"]
            assert config.get_poetry_extras() == ["extra2"]
            assert config.get_projects_dirs() == ["dir3"]

    def test_config_with_missing_keys(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            config_path = Path(td) / "pyproject.toml"
            config_path.write_text(
                """
[tool.other]
key = "value"
"""
            )
            config = Config(root_dir=td, path="pyproject.toml")
            assert config.get_private_packages() is None
            assert config.get_poetry_extras() is None
            assert config.get_projects_dirs() is None

    def test_config_with_empty_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            config_path = Path(td) / "pyproject.toml"
            config_path.write_text("")
            config = Config(root_dir=td, path="pyproject.toml")
            assert config.get_private_packages() is None
            assert config.get_poetry_extras() is None
            assert config.get_projects_dirs() is None

    def test_config_tool_versifier_takes_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            config_path = Path(td) / "pyproject.toml"
            config_path.write_text(
                """
[tool.versifier]
private_packages = ["tool_pkg"]

[versifier]
private_packages = ["versifier_pkg"]
"""
            )
            config = Config(root_dir=td, path="pyproject.toml")
            assert config.get_private_packages() == ["tool_pkg"]
