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

此命令将requirements.txt文件转换为Poetry格式。

```bash
versifier requirements-to-poetry --poetry-path <path_to_poetry> -r <requirements_files> -d <dev_requirements_files> -e <exclude_packages>
```

- `--poetry-path`: 指明Poetry的路径。默认为 "poetry"。
- `-r, --requirements`: 一个或多个requirements文件。
- `-d, --dev-requirements`: 一个或多个开发需求文件。
- `-e, --exclude`: 需要排除的包。

### poetry-to-requirements

此命令将Poetry依赖项导出到requirements.txt格式。

```bash
versifier poetry-to-requirements -o <output_file> --poetry-path <path_to_poetry> --exclude-specifiers --include-comments -d -E <extra_requirements> -m <markers>
```

- `-o, --output`: 指明输出文件。如果未提供，则输出打印到控制台。
- `--poetry-path`: 指明Poetry的路径。默认为 "poetry"。
- `--exclude-specifiers`: 排除说明符。
- `--include-comments`: 包括评论。
- `-d, --include-dev-requirements`: 包括开发需求。
- `-E, --extra-requirements`: 额外的需求。
- `-m, --markers`: 过滤标记。
- `-P, --private-packages`：私有包列表。

### extract-private-packages

此命令提取私有包。

```bash
versifier extract-private-packages --output <output_dir> --poetry-path <path_to_poetry> -E <extra_requirements> --exclude-file-patterns <exclude_files>
```

- `-o, --output`: 指明输出目录。默认为当前目录。
- `--poetry-path`: 指明Poetry的路径。默认为 "poetry"。
- `-E, --extra-requirements`: 额外的需求。
- `--exclude-file-patterns`: 需要排除的文件。
- `-P, --private-packages`：私有包列表。

### compile-private-packages

此命令编译私有包。

```bash
versifier compile-private-packages --output <output_dir> --poetry-path <path_to_poetry> --nuitka-path <path_to_nuitka3> -E <extra_requirements>
```

- `-o, --output`: 指明输出目录。默认为当前目录。
- `--poetry-path`: 指明Poetry的路径。默认为 "poetry"。
- `--nuitka-path`: 指明nuitka3的路径。默认为 "nuitka3"。
- `-E, --extra-requirements`: 额外的需求。
- `-P, --private-packages`：私有包列表。


### obfuscate-packages

此命令将指定包进行混淆，支持原地替换。

```bash
versifier obfuscate-packages --nuitka-path <path_to_nuitka3> --root-dir <root_dir> --output-dir <output_dir> -P <private_packages>
```

- `--nuitka-path`: 指明nuitka3的路径。默认为 "nuitka3"。
- `-r, --root`: 指明根目录。默认为当前目录。
- `-o, --output`: 指明输出目录。默认为当前目录。
- `-p, --private-packages`：私有包列表。

## License

此项目使用 MIT 许可证。有关详细信息，请参阅 LICENSE 文件。

## Contributing

我们欢迎各种形式的贡献，包括报告问题、提出新功能、改进文档或提交代码更改。如果你想要贡献，请查看 CONTRIBUTING.md 获取更多信息。