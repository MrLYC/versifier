import os
import tempfile
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

from versifier.uv import Uv


class TestUv:
    def test_init(self) -> None:
        uv = Uv()
        assert uv.uv_path == "uv"

    def test_init_with_custom_path(self) -> None:
        uv = Uv(uv_path="/custom/uv")
        assert uv.uv_path == "/custom/uv"

    @patch("versifier.uv.check_call")
    def test_add_packages(self, mock_check_call: MagicMock) -> None:
        uv = Uv()
        uv.add_packages(["requests", "flask"])
        mock_check_call.assert_called_once()
        args = mock_check_call.call_args[0][0]
        assert "uv" in args
        assert "add" in args
        assert "--no-sync" in args
        assert "requests" in args
        assert "flask" in args

    @patch("versifier.uv.check_call")
    def test_add_packages_dev(self, mock_check_call: MagicMock) -> None:
        uv = Uv()
        uv.add_packages(["pytest"], is_dev=True)
        mock_check_call.assert_called_once()
        args = mock_check_call.call_args[0][0]
        assert "--dev" in args

    @patch("versifier.uv.check_call")
    def test_add_packages_no_lock(self, mock_check_call: MagicMock) -> None:
        uv = Uv()
        uv.add_packages(["requests"], lock_only=False)
        mock_check_call.assert_called_once()
        args = mock_check_call.call_args[0][0]
        assert "--no-sync" not in args

    @patch("versifier.uv.check_call")
    def test_install(self, mock_check_call: MagicMock) -> None:
        uv = Uv()
        uv.install()
        mock_check_call.assert_called_once()
        args = mock_check_call.call_args[0][0]
        assert "uv" in args
        assert "sync" in args
        assert "--no-dev" in args

    @patch("versifier.uv.check_call")
    def test_install_with_dev(self, mock_check_call: MagicMock) -> None:
        uv = Uv()
        uv.install(include_dev_requirements=True)
        mock_check_call.assert_called_once()
        args = mock_check_call.call_args[0][0]
        assert "--no-dev" not in args

    @patch("versifier.uv.check_call")
    def test_install_with_extras(self, mock_check_call: MagicMock) -> None:
        uv = Uv()
        uv.install(extra_requirements=["extra1", "extra2"])
        mock_check_call.assert_called_once()
        args = mock_check_call.call_args[0][0]
        assert "--extra=extra1" in args
        assert "--extra=extra2" in args

    @patch("versifier.uv.check_call")
    def test_run_command(self, mock_check_call: MagicMock) -> None:
        uv = Uv()
        uv.run_command(["pip", "install", "requests"])
        mock_check_call.assert_called_once()
        args = mock_check_call.call_args[0][0]
        assert args == ["uv", "run", "pip", "install", "requests"]

    @patch("versifier.uv.check_call")
    def test_init_if_needed_when_lock_exists(self, mock_check_call: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as td:
            lock_path = Path(td) / "uv.lock"
            lock_path.write_text("")
            original_dir = os.getcwd()
            try:
                os.chdir(td)
                uv = Uv()
                uv.init_if_needed()
                mock_check_call.assert_not_called()
            finally:
                os.chdir(original_dir)

    @patch("versifier.uv.check_call")
    def test_init_if_needed_when_lock_not_exists(self, mock_check_call: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as td:
            original_dir = os.getcwd()
            try:
                os.chdir(td)
                uv = Uv()
                uv.init_if_needed()
                mock_check_call.assert_called_once()
                args = mock_check_call.call_args[0][0]
                assert "uv" in args
                assert "lock" in args
            finally:
                os.chdir(original_dir)

    @patch("versifier.uv.check_call")
    def test_export_requirements(self, mock_check_call: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as td:
            original_dir = os.getcwd()
            try:
                os.chdir(td)

                def side_effect(commands: list) -> None:
                    for cmd in commands:
                        if cmd.startswith("--output-file="):
                            req_path = cmd.split("=", 1)[1]
                            Path(req_path).write_text("requests==2.28.0\n")
                            break

                mock_check_call.side_effect = side_effect

                uv = Uv()
                rf = uv.export_requirements()
                assert rf is not None
                args = mock_check_call.call_args[0][0]
                assert "--no-hashes" in args
                assert "--no-dev" in args
            finally:
                os.chdir(original_dir)

    @patch("versifier.uv.check_call")
    def test_export_requirements_with_options(self, mock_check_call: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as td:
            original_dir = os.getcwd()
            try:
                os.chdir(td)

                def side_effect(commands: list) -> None:
                    for cmd in commands:
                        if cmd.startswith("--output-file="):
                            req_path = cmd.split("=", 1)[1]
                            Path(req_path).write_text("requests==2.28.0\n")
                            break

                mock_check_call.side_effect = side_effect

                uv = Uv()
                rf = uv.export_requirements(
                    include_dev_requirements=True,
                    extra_requirements=["extra1"],
                    with_credentials=True,
                )
                assert rf is not None
                args = mock_check_call.call_args[0][0]
                assert "--no-dev" not in args
                assert "--extra=extra1" in args
            finally:
                os.chdir(original_dir)
