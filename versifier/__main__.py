import logging
from functools import partial
from subprocess import check_call
from tempfile import TemporaryDirectory
from typing import List

import click

from versifier.poetry import Poetry

from .config import Config

logger = logging.getLogger(__name__)


@click.group()
def cli() -> None:
    logging.basicConfig(level=logging.INFO)


@cli.command()
@click.option("-r", "--requirements", multiple=True, default=[], help="requirements files")
@click.option("-d", "--dev-requirements", multiple=True, default=[], help="dev requirements files")
@click.option("-e", "--exclude", multiple=True, default=[], help="exclude packages")
@click.option("--poetry-path", default="poetry", help="path to poetry")
@click.option("--dry-run", is_flag=True, help="dry run")
def requirements_to_poetry(
    requirements: List[str],
    dev_requirements: List[str],
    exclude: List[str],
    poetry_path: str,
    dry_run: bool,
) -> None:
    def fake_check_call(commands: List[str]) -> None:
        logger.info("Would run: %s", commands)

    poetry = Poetry(poetry_path)
    poetry.add_from_requirements_txt(
        requirements,
        dev_requirements,
        exclude,
        fake_check_call if dry_run else check_call,
    )


@cli.command()
@click.option("-o", "--output", default="", help="output file")
@click.option("--poetry-path", default="poetry", help="path to poetry")
@click.option("--exclude-specifiers", is_flag=True, help="exclude specifiers")
@click.option("--include-comments", is_flag=True, help="include comments")
@click.option("-d", "--include-dev-requirements", is_flag=True, help="include dev requirements")
@click.option("-E", "--extra-requirements", multiple=True, default=[], help="extra requirements")
@click.option("-m", "--markers", multiple=True, default=[], help="markers")
def poetry_to_requirements(
    output: str,
    poetry_path: str,
    exclude_specifiers: bool,
    include_comments: bool,
    include_dev_requirements: bool,
    extra_requirements: List[str],
    markers: List[str],
) -> None:
    config = Config.from_toml()
    poetry = Poetry(poetry_path)
    fn = partial(
        poetry.export_to_requirements_txt,
        include_specifiers=not exclude_specifiers,
        include_comments=include_comments,
        exclude=config.private_packages,
        include_dev_requirements=include_dev_requirements,
        extra_requirements=extra_requirements,
        markers=markers,
    )

    if output == "":
        fn(callback=print)

    else:
        with open(output, "w") as f:
            fn(callback=lambda line: f.write(line + "\n"))


@cli.command()
@click.option("--output", default=".", help="output dir")
@click.option("--poetry-path", default="poetry", help="path to poetry")
@click.option("-E", "--extra-requirements", multiple=True, default=[], help="extra requirements")
def extract_private_packages(
    output: str,
    poetry_path: str,
    extra_requirements: List[str],
) -> None:
    config = Config.from_toml()
    poetry = Poetry(poetry_path)

    poetry.extract_packages(output_dir=output, packages=config.private_packages, extra_requirements=extra_requirements)


if __name__ == "__main__":
    cli()
