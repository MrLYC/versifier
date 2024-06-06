import argparse
from subprocess import check_call
from typing import Callable, Iterable, List

from requirements import parse as parse_requirements


def fake_check_call(commands: List[str]) -> None:
    print(" ".join(commands))


def iter_requirements(requirements: List[str]) -> Iterable[str]:
    for n in requirements:
        with open(n, "r") as f:
            for r in parse_requirements(f):
                if not r.specs:
                    yield r.name
                else:
                    specifier = ",".join(f"{i[0]}{i[1]}" for i in r.specs)
                    yield f"{r.name}{specifier}"


def run(requirements: List[str], dev_requirements: List[str], callback: Callable) -> None:
    commands = ["poetry", "add"]

    requirements_to_add = list(iter_requirements(requirements))

    if requirements_to_add:
        callback(commands + requirements_to_add)

    dev_requirements_to_add = list(iter_requirements(dev_requirements))

    if dev_requirements_to_add:
        callback("Adding dev requirements")
        callback(commands + ["--dev"] + requirements_to_add)


def main() -> None:
    parser = argparse.ArgumentParser(description="Process some requirements.")
    parser.add_argument("-r", "--requirements", nargs="+", default=[], help="requirements files")
    parser.add_argument("-d", "--dev-requirements", nargs="+", default=[], help="dev requirements files")
    parser.add_argument("--dry-run", action="store_true", default=False, help="dry run")

    args = parser.parse_args()

    if args.dry_run:
        callback = fake_check_call
    else:
        callback = check_call  # type: ignore

    run(args.requirements, args.dev_requirements, callback)


if __name__ == "__main__":
    main()
