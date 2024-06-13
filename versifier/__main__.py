import logging
from subprocess import check_call
from typing import Callable, List

import click

from versifier import poetry

logger = logging.getLogger(__name__)


@click.group()
def cli() -> None:
    logging.basicConfig(level=logging.INFO)


@cli.command()
@click.option("-r", "--requirements", multiple=True, default=[], help="requirements files")
@click.option("-d", "--dev-requirements", multiple=True, default=[], help="dev requirements files")
@click.option("--poetry-path", default="poetry", help="path to poetry")
@click.option("--dry-run", is_flag=True, help="dry run")
def requirements_to_poetry(
    requirements: List[str],
    dev_requirements: List[str],
    poetry_path: str,
    dry_run: bool,
) -> None:
    def fake_check_call(commands: List[str]) -> None:
        logger.info("Would run: %s", commands)

    poetry.add_from_requirements_txt(
        poetry_path,
        requirements,
        dev_requirements,
        fake_check_call if dry_run else check_call,
    )


if __name__ == "__main__":
    cli()
