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

### requirements_to_poetry

这个命令将 requirements.txt 转化为 Poetry 的 pyproject.toml。

使用方法：

```shell
requirements_to_poetry -r <requirements> -d <dev_requirements> -e <exclude>
```

参数说明：

- `-r, --requirements`：指定一个或多个 requirements 文件。
- `-d, --dev-requirements`：指定一个或多个 dev requirements 文件。
- `-e, --exclude`：指定需要排除的包。

### poetry_to_requirements

这个命令将 Poetry 的 pyproject.toml 导出为 requirements.txt。

使用方法：

```shell
poetry_to_requirements -o <output> --exclude-specifiers --include-comments -d -E <extra_requirements> -m <markers>
```

参数说明：

- `-o, --output`：输出文件的路径。如果不指定，将直接打印到控制台。
- `--exclude-specifiers`：如果指定，将排除版本规定。
- `--include-comments`：如果指定，将包含注释。
- `-d, --include-dev-requirements`：如果指定，将包含 dev requirements。
- `-E, --extra-requirements`：指定额外的 requirements。
- `-m, --markers`：指定 markers。

### extract_private_packages

这个命令用于提取私有包。

使用方法：

```shell
extract_private_packages --output <output_dir> --poetry-path <poetry_path> -E <extra_requirements> --exclude-file-patterns <exclude_patterns>
```

参数说明：

- `--output`：输出目录的路径。
- `--poetry-path`：Poetry 的路径。
- `-E, --extra-requirements`：指定额外的 requirements。
- `--exclude-file-patterns`：指定需要排除的文件模式。

## License

此项目使用 MIT 许可证。有关详细信息，请参阅 LICENSE 文件。

## Contributing

我们欢迎各种形式的贡献，包括报告问题、提出新功能、改进文档或提交代码更改。如果你想要贡献，请查看 CONTRIBUTING.md 获取更多信息。