import functools
import logging
import os
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable, List

import click

from versifier import core

from .compiler import Compiler
from .config import Config
from .poetry import Poetry

logger = logging.getLogger(__name__)


@dataclass
class Context:
    root_path: str
    config_path: str
    poetry_path: str
    nuitka_path: str

    @property
    def poetry(self) -> Poetry:
        return Poetry(self.poetry_path)

    @property
    def compiler(self) -> Compiler:
        return Compiler(self.nuitka_path)

    @property
    def config(self) -> Config:
        return Config(path=self.config_path)

    @property
    def root_dir(self) -> Path:
        return Path(self.root_path)

    @classmethod
    def wrapper(cls, func: Callable) -> Callable:
        @click.option("-c", "--config", default="pyproject.toml", help="config file")
        @click.option("-r", "--root", default=".", help="root dir")
        @click.option("--poetry-path", default="poetry", help="path to poetry")
        @click.option("--nuitka-path", default="nuitka3", help="path to nuitka3")
        @click.option("--log-level", default="INFO", help="log level")
        @functools.wraps(func)
        def wrapped(
            config: str,
            root: str,
            poetry_path: str,
            nuitka_path: str,
            log_level: str,
            *args: Any,
            **kwargs: Any,
        ) -> None:
            logging.basicConfig(level=logging.getLevelName(log_level))
            os.chdir(root)

            ctx = cls(
                root_path=root,
                config_path=config,
                poetry_path=poetry_path,
                nuitka_path=nuitka_path,
            )
            func(ctx=ctx, *args, **kwargs)

        return wrapped


@click.group()
def cli() -> None:
    pass


@cli.command(help="convert requirements to poetry")
@click.option("-R", "--requirements", multiple=True, default=[], help="requirements files")
@click.option("-d", "--dev-requirements", multiple=True, default=[], help="dev requirements files")
@click.option("-e", "--exclude", multiple=True, default=[], help="exclude packages")
@click.option("--add-only", is_flag=True, help="add only")
@Context.wrapper
def requirements_to_poetry(
    ctx: Context,
    requirements: List[str],
    dev_requirements: List[str],
    exclude: List[str],
    add_only: bool,
) -> None:
    poetry = ctx.poetry
    if not add_only:
        poetry.init_if_needed()

    ext = core.DependencyManager(poetry)
    ext.add_from_requirements_txt(
        requirements,
        dev_requirements,
        exclude,
    )


@cli.command(help="convert poetry to requirements")
@click.option("-o", "--output", default="requirements.txt", help="output file")
@click.option("--exclude-specifiers", is_flag=True, help="exclude specifiers")
@click.option("--include-comments", is_flag=True, help="include comments")
@click.option("-d", "--include-dev-requirements", is_flag=True, help="include dev requirements")
@click.option("-E", "--extra-requirements", multiple=True, default=[], help="extra requirements")
@click.option("-m", "--markers", multiple=True, default=[], help="markers")
@click.option("-P", "--private-packages", multiple=True, default=[], help="private packages")
@Context.wrapper
def poetry_to_requirements(
    ctx: Context,
    output: str,
    exclude_specifiers: bool,
    include_comments: bool,
    include_dev_requirements: bool,
    extra_requirements: List[str],
    markers: List[str],
    private_packages: List[str],
) -> None:
    conf = ctx.config
    if not private_packages:
        private_packages = conf.get_private_packages() or []

    ext = core.DependencyExporter(ctx.poetry)
    fn = partial(
        ext.export_to_requirements_txt,
        include_specifiers=not exclude_specifiers,
        include_comments=include_comments,
        exclude=private_packages,
        include_dev_requirements=include_dev_requirements,
        extra_requirements=extra_requirements,
        markers=markers,
    )

    if output == "":
        fn(callback=print)

    else:
        with open(output, "w") as f:
            fn(callback=lambda line: f.write(line + "\n"))


@cli.command(help="extract private packages")
@click.option("-o", "--output", default="output", help="output dir")
@click.option("-E", "--extra-requirements", multiple=True, default=[], help="extra requirements")
@click.option("--exclude-file-patterns", multiple=True, default=[], help="exclude files")
@click.option("-P", "--private-packages", multiple=True, default=[], help="private packages")
@Context.wrapper
def extract_private_packages(
    ctx: Context,
    output: str,
    extra_requirements: List[str],
    exclude_file_patterns: List[str],
    private_packages: List[str],
) -> None:
    conf = ctx.config

    if not private_packages:
        private_packages = conf.get_private_packages() or []

    if not private_packages:
        raise click.UsageError("No private packages found")

    os.makedirs(output, exist_ok=True)
    ext = core.PackageExtractor(ctx.poetry)
    ext.extract_packages(
        output_dir=output,
        packages=private_packages,
        extra_requirements=extra_requirements,
        exclude_file_patterns=exclude_file_patterns,
    )


@cli.command(help="obfuscate project dirs")
@click.option("-o", "--output", default="output", help="output dir")
@click.option("-d", "--sub-dirs", multiple=True, default=None, help="included sub dirs")
@click.option("--exclude-packages", multiple=True, default=["*.tests"], help="exclude packages")
@Context.wrapper
def obfuscate_project_dirs(
    ctx: Context,
    output: str,
    sub_dirs: List[str],
    exclude_packages: List[str],
) -> None:
    root_dir = ctx.root_dir
    conf = ctx.config

    if not sub_dirs:
        sub_dirs = conf.get_projects_dirs() or ["."]

    os.makedirs(output, exist_ok=True)
    for d in sub_dirs:
        path = root_dir.joinpath(d)
        ext = core.PackageObfuscator(compiler=ctx.compiler)
        ext.obfuscate_packages(
            packages=set(i.parent.name for i in path.glob("*/__init__.py")),
            root_dir=str(path),
            output_dir=output,
            exclude_packages=exclude_packages,
        )


@cli.command(help="obfuscate private packages")
@click.option("-o", "--output", default="output", help="output dir")
@click.option("-E", "--extra-requirements", multiple=True, default=[], help="extra requirements")
@click.option("-P", "--private-packages", multiple=True, default=[], help="private packages")
@Context.wrapper
def obfuscate_private_packages(
    ctx: Context,
    output: str,
    extra_requirements: List[str],
    private_packages: List[str],
) -> None:
    conf = ctx.config

    if not private_packages:
        private_packages = conf.get_private_packages() or []

    if not private_packages:
        raise click.UsageError("No private packages found")

    os.makedirs(output, exist_ok=True)
    with TemporaryDirectory() as td:
        extractor = core.PackageExtractor(ctx.poetry)
        extractor.extract_packages(
            output_dir=td,
            packages=private_packages,
            extra_requirements=extra_requirements,
        )

        obfuscator = core.PackageObfuscator(compiler=ctx.compiler)
        obfuscator.obfuscate_packages(
            packages=private_packages,
            root_dir=td,
            output_dir=output,
        )


@cli.command(help="show command help details")
@click.pass_context
def command_details(ctx: click.Context) -> None:
    for name, command in cli.commands.items():
        print(f"----- {name} -----")
        print(command.get_help(ctx))
        print("")


if __name__ == "__main__":
    cli()
