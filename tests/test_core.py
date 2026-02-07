import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from versifier.core import DependencyExporter, DependencyManager, PackageExtractor, PackageObfuscator


class TestDependencyManager:
    @patch("versifier.core.RequirementsFile")
    def test_merge_requirements(self, mock_rf_class: MagicMock) -> None:
        mock_rf = MagicMock()
        mock_req1 = MagicMock()
        mock_req1.req = "requests==2.28.0"
        mock_req2 = MagicMock()
        mock_req2.req = "flask>=2.0.0"
        mock_rf.requirements = [mock_req1, mock_req2]
        mock_rf.filter.return_value = mock_rf
        mock_rf_class.from_file.return_value = mock_rf

        poetry = MagicMock()
        manager = DependencyManager(poetry=poetry)
        result = manager._merge_requirements(["requirements.txt"])

        assert len(result) == 2

    @patch("versifier.core.RequirementsFile")
    def test_merge_requirements_with_exclude(self, mock_rf_class: MagicMock) -> None:
        mock_rf = MagicMock()
        mock_req1 = MagicMock()
        mock_req1.req = "requests==2.28.0"
        mock_rf.requirements = [mock_req1]
        mock_rf.filter.return_value = mock_rf
        mock_rf_class.from_file.return_value = mock_rf

        poetry = MagicMock()
        manager = DependencyManager(poetry=poetry)
        manager._merge_requirements(["requirements.txt"], exclude=["flask"])

        mock_rf.filter.assert_called_once()

    @patch("versifier.core.RequirementsFile")
    def test_add_from_requirements_txt(self, mock_rf_class: MagicMock) -> None:
        mock_rf = MagicMock()
        mock_req = MagicMock()
        mock_req.req = "requests==2.28.0"
        mock_rf.requirements = [mock_req]
        mock_rf.filter.return_value = mock_rf
        mock_rf_class.from_file.return_value = mock_rf

        poetry = MagicMock()
        manager = DependencyManager(poetry=poetry)
        manager.add_from_requirements_txt(requirements=["requirements.txt"], dev_requirements=[], exclude=[])

        poetry.add_packages.assert_called_once()

    @patch("versifier.core.RequirementsFile")
    def test_add_from_requirements_txt_with_dev(self, mock_rf_class: MagicMock) -> None:
        mock_rf = MagicMock()
        mock_req = MagicMock()
        mock_req.req = "pytest==7.0.0"
        mock_rf.requirements = [mock_req]
        mock_rf.filter.return_value = mock_rf
        mock_rf_class.from_file.return_value = mock_rf

        poetry = MagicMock()
        manager = DependencyManager(poetry=poetry)
        manager.add_from_requirements_txt(requirements=[], dev_requirements=["dev-requirements.txt"], exclude=[])

        poetry.add_packages.assert_called_once_with({"pytest==7.0.0"}, is_dev=True)

    @patch("versifier.core.RequirementsFile")
    def test_add_from_requirements_txt_empty(self, mock_rf_class: MagicMock) -> None:
        mock_rf = MagicMock()
        mock_rf.requirements = []
        mock_rf.filter.return_value = mock_rf
        mock_rf_class.from_file.return_value = mock_rf

        poetry = MagicMock()
        manager = DependencyManager(poetry=poetry)
        manager.add_from_requirements_txt(requirements=["requirements.txt"], dev_requirements=[], exclude=[])

        poetry.add_packages.assert_not_called()


class TestDependencyExporter:
    def test_export_to_requirements_txt(self) -> None:
        mock_rf = MagicMock()
        mock_req = MagicMock()
        mock_req.line = "requests==2.28.0  # comment"
        mock_req.req = MagicMock()
        mock_req.req.__str__ = MagicMock(return_value="requests==2.28.0")
        mock_req.req.name = "requests"
        mock_rf.requirements = [mock_req]
        mock_rf.filter.return_value = mock_rf

        poetry = MagicMock()
        poetry.export_requirements.return_value = mock_rf

        exporter = DependencyExporter(poetry=poetry)
        output = []
        exporter.export_to_requirements_txt(callback=output.append)

        assert len(output) == 1
        assert "requests" in output[0]

    def test_export_to_requirements_txt_with_comments(self) -> None:
        mock_rf = MagicMock()
        mock_req = MagicMock()
        mock_req.line = "requests==2.28.0  # comment"
        mock_req.req = MagicMock()
        mock_req.req.__str__ = MagicMock(return_value="requests==2.28.0")
        mock_req.req.name = "requests"
        mock_rf.requirements = [mock_req]
        mock_rf.filter.return_value = mock_rf

        poetry = MagicMock()
        poetry.export_requirements.return_value = mock_rf

        exporter = DependencyExporter(poetry=poetry)
        output = []
        exporter.export_to_requirements_txt(include_comments=True, callback=output.append)

        assert output[0] == "requests==2.28.0  # comment"

    def test_export_to_requirements_txt_without_specifiers(self) -> None:
        mock_rf = MagicMock()
        mock_req = MagicMock()
        mock_req.line = "requests==2.28.0"
        mock_req.req = MagicMock()
        mock_req.req.__str__ = MagicMock(return_value="requests==2.28.0")
        mock_req.req.name = "requests"
        mock_rf.requirements = [mock_req]
        mock_rf.filter.return_value = mock_rf

        poetry = MagicMock()
        poetry.export_requirements.return_value = mock_rf

        exporter = DependencyExporter(poetry=poetry)
        output = []
        exporter.export_to_requirements_txt(include_specifiers=False, callback=output.append)

        assert output[0] == "requests"


class TestPackageExtractor:
    def test_do_clean_directory(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dist_info = Path(td) / "pkg.dist-info"
            dist_info.mkdir()
            (dist_info / "METADATA").write_text("")

            pycache = Path(td) / "__pycache__"
            pycache.mkdir()
            (pycache / "module.pyc").write_text("")

            poetry = MagicMock()
            extractor = PackageExtractor(poetry=poetry)
            extractor._do_clean_directory(td, ["*/*.dist-info", "*/__pycache__"])

            assert not dist_info.exists()
            assert not pycache.exists()

    def test_do_clean_directory_no_match(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            keep_dir = Path(td) / "keep"
            keep_dir.mkdir()
            (keep_dir / "file.txt").write_text("")

            poetry = MagicMock()
            extractor = PackageExtractor(poetry=poetry)
            extractor._do_clean_directory(td, ["*/*.dist-info"])

            assert keep_dir.exists()

    @patch("versifier.core.os.listdir")
    @patch("versifier.core.shutil.move")
    def test_extract_packages(self, mock_move: MagicMock, mock_listdir: MagicMock) -> None:
        mock_rf = MagicMock()
        mock_rf.requirements = []
        mock_rf.filter.return_value = mock_rf
        mock_rf.dump_to = MagicMock()

        poetry = MagicMock()
        poetry.export_requirements.return_value = mock_rf
        poetry.run_command = MagicMock()

        mock_listdir.return_value = []

        with tempfile.TemporaryDirectory() as td:
            output_dir = Path(td) / "output"
            output_dir.mkdir()

            extractor = PackageExtractor(poetry=poetry)
            extractor.extract_packages(output_dir=str(output_dir), packages=["pkg1"])

            poetry.export_requirements.assert_called_once()
            poetry.run_command.assert_called_once()


class TestPackageObfuscator:
    @patch("versifier.core.shutil.move")
    @patch("versifier.core.PackageStubGenerator")
    def test_obfuscate_packages(self, mock_stub_gen_class: MagicMock, mock_move: MagicMock) -> None:
        mock_stub_gen = MagicMock()
        mock_stub_gen_class.return_value = mock_stub_gen

        compiler = MagicMock()

        with tempfile.TemporaryDirectory() as td:
            root_dir = Path(td) / "root"
            root_dir.mkdir()
            output_dir = Path(td) / "output"
            output_dir.mkdir()

            obfuscator = PackageObfuscator(compiler=compiler)
            obfuscator.obfuscate_packages(packages=["pkg1"], root_dir=str(root_dir), output_dir=str(output_dir))

            compiler.compile_packages.assert_called_once()
            mock_stub_gen.generate.assert_called_once()

    @patch("versifier.core.shutil.move")
    @patch("versifier.core.PackageStubGenerator")
    def test_obfuscate_packages_with_variants(self, mock_stub_gen_class: MagicMock, mock_move: MagicMock) -> None:
        mock_stub_gen = MagicMock()
        mock_stub_gen_class.return_value = mock_stub_gen

        compiler = MagicMock()

        with tempfile.TemporaryDirectory() as td:
            root_dir = Path(td) / "root"
            root_dir.mkdir()
            output_dir = Path(td) / "output"
            output_dir.mkdir()

            obfuscator = PackageObfuscator(compiler=compiler)
            obfuscator.obfuscate_packages(packages=["my-pkg"], root_dir=str(root_dir), output_dir=str(output_dir))

            call_args = compiler.compile_packages.call_args
            packages = call_args[1]["packages"] if "packages" in call_args[1] else call_args[0][2]
            assert "my-pkg" in packages
            assert "my_pkg" in packages
