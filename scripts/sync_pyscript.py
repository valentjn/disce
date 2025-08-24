#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Make sure pyscript.toml is up to date."""

import argparse
import logging
import sys
from pathlib import Path

import tomlkit
import tomlkit.items
from packaging.requirements import Requirement

_logger = logging.getLogger(__name__)


def main() -> None:
    """Make sure pyscript.toml is up to date."""
    arguments = parse_arguments()
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    old_toml = read_config_toml()
    config = tomlkit.parse(old_toml)
    update_files(config)
    update_packages(config)
    write_config(config, old_toml, check=arguments.check)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action=argparse.BooleanOptionalAction,
        help="only check if pyscript.toml is up to date, exit with 1 if not",
    )
    return parser.parse_args()


def get_root_dir() -> Path:
    """Get the root directory of the project."""
    return Path(__file__).parent.parent


def get_python_dir() -> Path:
    """Get the path to the python directory."""
    return get_root_dir() / "src/python"


def read_config_toml() -> str:
    """Read the pyscript.toml file."""
    return (get_python_dir() / "pyscript.toml").read_text()


def update_files(config: tomlkit.TOMLDocument) -> None:
    """Update the [files] section of the pyscript.toml file."""
    python_dir = get_python_dir()
    disce_files = sorted(entry for entry in (python_dir / "disce").rglob("*") if entry.is_file())
    config["files"] = {str(file.relative_to(python_dir).as_posix()): "./disce/" for file in disce_files}


def update_packages(config: tomlkit.TOMLDocument) -> None:
    """Update the [packages] section of the pyscript.toml file."""
    pyproject_toml = tomlkit.parse((get_root_dir() / "pyproject.toml").read_text())
    project = pyproject_toml["project"]
    if not isinstance(project, tomlkit.items.Table):
        msg = "project section is not a table"
        raise TypeError(msg)
    dependencies = project["dependencies"]
    config["packages"] = [Requirement(dependency).name for dependency in dependencies.unwrap()]


def write_config(config: tomlkit.TOMLDocument, old_toml: str, *, check: bool = False) -> None:
    """Write the pyscript.toml file if it has changed."""
    new_toml = tomlkit.dumps(config)
    if new_toml == old_toml:
        _logger.info("pyscript.toml is up to date")
        return
    if check:
        _logger.error("pyscript.toml is out of date")
        sys.exit(1)
    (get_python_dir() / "pyscript.toml").write_text(new_toml)


if __name__ == "__main__":
    main()
