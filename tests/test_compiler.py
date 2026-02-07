import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from versifier.compiler import Compiler, Cython, Nuitka3, SmartCompiler


class TestNuitka3:
    def test_init(self) -> None:
        nuitka = Nuitka3()
        assert nuitka.nuitka_path == "nuitka3"

    def test_init_with_custom_path(self) -> None:
        nuitka = Nuitka3(nuitka_path="/custom/nuitka3")
        assert nuitka.nuitka_path == "/custom/nuitka3"

    @patch("versifier.compiler.check_call")
    def test_compile_package(self, mock_check_call: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as td:
            package_path = Path(td) / "mypackage"
            package_path.mkdir()
            (package_path / "__init__.py").write_text("")

            nuitka = Nuitka3()
            nuitka._compile_package(output_dir=td, package_path=str(package_path))

            mock_check_call.assert_called_once()
            args = mock_check_call.call_args[0][0]
            assert "nuitka3" in args
            assert f"--output-dir={td}" in args
            assert "--module" in args
            assert "mypackage" in args

    @patch("versifier.compiler.check_call")
    def test_compile_package_with_nofollow(self, mock_check_call: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as td:
            package_path = Path(td) / "mypackage"
            package_path.mkdir()
            (package_path / "__init__.py").write_text("")

            nuitka = Nuitka3()
            nuitka._compile_package(output_dir=td, package_path=str(package_path), nofollow_import_to=["pkg1", "pkg2"])

            mock_check_call.assert_called_once()
            args = mock_check_call.call_args[0][0]
            assert "--nofollow-import-to=pkg1" in args
            assert "--nofollow-import-to=pkg2" in args

    @patch("versifier.compiler.check_call")
    def test_compile_packages_directory(self, mock_check_call: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as td:
            source_dir = Path(td) / "source"
            source_dir.mkdir()
            package_path = source_dir / "mypackage"
            package_path.mkdir()
            (package_path / "__init__.py").write_text("")

            output_dir = Path(td) / "output"
            output_dir.mkdir()

            nuitka = Nuitka3()
            nuitka.compile_packages(source_dir=str(source_dir), output_dir=str(output_dir), packages=["mypackage"])

            mock_check_call.assert_called_once()

    @patch("versifier.compiler.check_call")
    def test_compile_packages_file(self, mock_check_call: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as td:
            source_dir = Path(td) / "source"
            source_dir.mkdir()
            (source_dir / "mymodule.py").write_text("x = 1")

            output_dir = Path(td) / "output"
            output_dir.mkdir()

            nuitka = Nuitka3()
            nuitka.compile_packages(source_dir=str(source_dir), output_dir=str(output_dir), packages=["mymodule"])

            mock_check_call.assert_called_once()

    @patch("versifier.compiler.check_call")
    def test_compile_packages_nonexistent(self, mock_check_call: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as td:
            source_dir = Path(td) / "source"
            source_dir.mkdir()

            output_dir = Path(td) / "output"
            output_dir.mkdir()

            nuitka = Nuitka3()
            nuitka.compile_packages(source_dir=str(source_dir), output_dir=str(output_dir), packages=["nonexistent"])

            mock_check_call.assert_not_called()


class TestCython:
    @patch("versifier.compiler.setup")
    @patch("versifier.compiler.cythonize")
    def test_compile_packages_directory(self, mock_cythonize: MagicMock, mock_setup: MagicMock) -> None:
        mock_cythonize.return_value = []
        with tempfile.TemporaryDirectory() as td:
            source_dir = Path(td) / "source"
            source_dir.mkdir()
            package_path = source_dir / "mypackage"
            package_path.mkdir()
            (package_path / "__init__.py").write_text("")
            (package_path / "module.py").write_text("x = 1")

            output_dir = Path(td) / "output"
            output_dir.mkdir()

            cython = Cython()
            cython.compile_packages(source_dir=str(source_dir), output_dir=str(output_dir), packages=["mypackage"])

            mock_cythonize.assert_called_once()
            mock_setup.assert_called_once()

    @patch("versifier.compiler.setup")
    @patch("versifier.compiler.cythonize")
    def test_compile_packages_file(self, mock_cythonize: MagicMock, mock_setup: MagicMock) -> None:
        mock_cythonize.return_value = []
        with tempfile.TemporaryDirectory() as td:
            source_dir = Path(td) / "source"
            source_dir.mkdir()
            (source_dir / "mymodule.py").write_text("x = 1")

            output_dir = Path(td) / "output"
            output_dir.mkdir()

            cython = Cython()
            cython.compile_packages(source_dir=str(source_dir), output_dir=str(output_dir), packages=["mymodule"])

            mock_cythonize.assert_called_once()
            mock_setup.assert_called_once()

    @patch("versifier.compiler.setup")
    @patch("versifier.compiler.cythonize")
    def test_compile_packages_nonexistent(self, mock_cythonize: MagicMock, mock_setup: MagicMock) -> None:
        mock_cythonize.return_value = []
        with tempfile.TemporaryDirectory() as td:
            source_dir = Path(td) / "source"
            source_dir.mkdir()

            output_dir = Path(td) / "output"
            output_dir.mkdir()

            cython = Cython()
            cython.compile_packages(source_dir=str(source_dir), output_dir=str(output_dir), packages=["nonexistent"])

            mock_cythonize.assert_called_once()
            mock_setup.assert_called_once()


class TestSmartCompiler:
    def test_init(self) -> None:
        compiler1 = MagicMock(spec=Compiler)
        compiler2 = MagicMock(spec=Compiler)
        smart = SmartCompiler(compilers=[compiler1, compiler2])
        assert len(smart.compilers) == 2

    def test_compile_packages_success(self) -> None:
        compiler1 = MagicMock(spec=Compiler)
        smart = SmartCompiler(compilers=[compiler1])

        smart.compile_packages(source_dir="/src", output_dir="/out", packages=["pkg1", "pkg2"])

        assert compiler1.compile_packages.call_count == 2

    def test_compile_packages_fallback(self) -> None:
        compiler1 = MagicMock(spec=Compiler)
        compiler1.compile_packages.side_effect = Exception("Failed")
        compiler2 = MagicMock(spec=Compiler)

        smart = SmartCompiler(compilers=[compiler1, compiler2])
        smart.compile_packages(source_dir="/src", output_dir="/out", packages=["pkg1"])

        compiler1.compile_packages.assert_called_once()
        compiler2.compile_packages.assert_called_once()

    def test_compile_packages_all_fail(self) -> None:
        compiler1 = MagicMock(spec=Compiler)
        compiler1.compile_packages.side_effect = Exception("Failed")
        compiler2 = MagicMock(spec=Compiler)
        compiler2.compile_packages.side_effect = Exception("Failed")

        smart = SmartCompiler(compilers=[compiler1, compiler2])
        smart.compile_packages(source_dir="/src", output_dir="/out", packages=["pkg1"])

        compiler1.compile_packages.assert_called_once()
        compiler2.compile_packages.assert_called_once()
