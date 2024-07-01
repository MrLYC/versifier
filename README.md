# versifier

[![Release](https://img.shields.io/github/v/release/mrlyc/versifier)](https://img.shields.io/github/v/release/mrlyc/versifier)
[![Build status](https://img.shields.io/github/actions/workflow/status/mrlyc/versifier/main.yml?branch=main)](https://github.com/mrlyc/versifier/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/mrlyc/versifier/branch/main/graph/badge.svg)](https://codecov.io/gh/mrlyc/versifier)
[![Commit activity](https://img.shields.io/github/commit-activity/m/mrlyc/versifier)](https://img.shields.io/github/commit-activity/m/mrlyc/versifier)
[![License](https://img.shields.io/github/license/mrlyc/versifier)](https://img.shields.io/github/license/mrlyc/versifier)

## Overview

这个项目提供了一套命令行工具集，主要用于处理 Python 项目的依赖管理。主要功能包括：
- 将 requirements.txt 转化为 Poetry 的 pyproject.toml
- 将 Poetry 的 pyproject.toml 导出为 requirements.txt
- 将私有包提取到指定目录

## Installation

使用 pip 来安装这个项目：

```shell
pip install versifier
```

## Commands
### requirements-to-poetry

将 requirements 转换为 poetry。

```bash
versifier requirements-to-poetry --requirements <requirements_files> --dev-requirements <dev_requirements_files> --exclude <exclude_packages> --add-only --config <config_file> --root <root_dir> --poetry-path <path_to_poetry> --nuitka-path <path_to_nuitka3> --log-level <log_level>
```

参数说明：
- `-R, --requirements`: 指定 requirements 文件。默认为当前目录的 requirements.txt。
- `-d, --dev-requirements`: 指定开发环境的 requirements 文件。默认为当前目录的 dev-requirements.txt。
- `-e, --exclude`: 指定要排除的包。
- `--add-only`: 只添加指定的包，而不删除任何现有的包。
- `-c, --config`: 指定配置文件。
- `-r, --root`: 指定根目录。默认为当前目录。
- `--poetry-path`: 指定 poetry 的路径。默认为 "poetry"。
- `--nuitka-path`: 指定 nuitka3 的路径。默认为 "nuitka3"。
- `--log-level`: 指定日志级别。

### poetry-to-requirements

将 poetry 转换为 requirements。

```bash
versifier poetry-to-requirements --output <output_file> --exclude-specifiers --include-comments --include-dev-requirements --extra-requirements <extra_requirements> --markers <markers> --private-packages <private_packages> --config <config_file> --root <root_dir> --poetry-path <path_to_poetry> --nuitka-path <path_to_nuitka3> --log-level <log_level>
```

参数说明：
- `-o, --output`: 指定输出文件。
- `--exclude-specifiers`: 排除指定的包。
- `--include-comments`: 包含注释。
- `-d, --include-dev-requirements`: 包含开发环境的 requirements。
- `-E, --extra-requirements`: 指定额外的 requirements。
- `-m, --markers`: 指定标记。
- `-P, --private-packages`: 指定私有包。
- `-c, --config`: 指定配置文件。
- `-r, --root`: 指定根目录。默认为当前目录。
- `--poetry-path`: 指定 poetry 的路径。默认为 "poetry"。
- `--nuitka-path`: 指定 nuitka3 的路径。默认为 "nuitka3"。
- `--log-level`: 指定日志级别。

### extract-private-packages

提取私有包。

```bash
versifier extract-private-packages --output <output_dir> --extra-requirements <extra_requirements> --exclude-file-patterns <exclude_files> --private-packages <private_packages> --config <config_file> --root <root_dir> --poetry-path <path_to_poetry> --nuitka-path <path_to_nuitka3> --log-level <log_level>
```

参数说明：
- `-o, --output`: 指定输出目录。默认为当前目录。
- `-E, --extra-requirements`: 指定额外的 requirements。
- `--exclude-file-patterns`: 指定要排除的文件模式。
- `-P, --private-packages`: 指定要提取的私有包列表。
- `-c, --config`: 指定配置文件。
- `-r, --root`: 指定根目录。默认为当前目录。
- `--poetry-path`: 指定 poetry 的路径。默认为 "poetry"。
- `--nuitka-path`: 指定 nuitka3 的路径。默认为 "nuitka3"。
- `--log-level`: 指定日志级别。

### obfuscate-project-dirs

混淆项目目录。

```bash
versifier obfuscate-project-dirs --output <output_dir> --sub-dirs <included_sub_dirs> --exclude-packages <exclude_packages> --config <config_file> --root <root_dir> --poetry-path <path_to_poetry> --nuitka-path <path_to_nuitka3> --log-level <log_level>
```

参数说明：
- `-o, --output`: 指定输出目录。默认为当前目录。
- `-d, --sub-dirs`: 指定要包含的子目录。
- `--exclude-packages`: 指定要排除的包。
- `-c, --config`: 指定配置文件。
- `-r, --root`: 指定根目录。默认为当前目录。
- `--poetry-path`: 指定 poetry 的路径。默认为 "poetry"。
- `--nuitka-path`: 指定 nuitka3 的路径。默认为 "nuitka3"。
- `--log-level`: 指定日志级别。

### obfuscate-private-packages

混淆私有包。

```bash
versifier obfuscate-private-packages --output <output_dir> --extra-requirements <extra_requirements> --private-packages <private_packages> --config <config_file> --root <root_dir> --poetry-path <path_to_poetry> --nuitka-path <path_to_nuitka3> --log-level <log_level>
```

参数说明：
- `-o, --output`: 指定输出目录。默认为当前目录。
- `-E, --extra-requirements`: 指定额外的 requirements。
- `-P, --private-packages`: 指定要混淆的私有包列表。
- `-c, --config`: 指定配置文件。
- `-r, --root`: 指定根目录。默认为当前目录。
- `--poetry-path`: 指定 poetry 的路径。默认为 "poetry"。
- `--nuitka-path`: 指定 nuitka3 的路径。默认为 "nuitka3"。
- `--log-level`: 指定日志级别。


## License

此项目使用 MIT 许可证。有关详细信息，请参阅 LICENSE 文件。

## Contributing

我们欢迎各种形式的贡献，包括报告问题、提出新功能、改进文档或提交代码更改。如果你想要贡献，请查看 CONTRIBUTING.md 获取更多信息。