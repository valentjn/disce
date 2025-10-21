#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import ast
import re
import shutil
import sys
from collections.abc import Generator
from datetime import timedelta
from pathlib import Path

import disce
import pytest
import tomlkit
import tomlkit.items
from selenium.webdriver import Firefox

from disce_tests.selenium import browsers, outputs, servers


@pytest.fixture(scope="session")
def injected_server_root_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_dir = _copy_disce_with_tests(tmp_path_factory.mktemp("server_root_dir") / "root")
    _inject_tests_into_index_html(root_dir / "index.html")
    _inject_tests_into_pyscript_toml(root_dir / "python")
    return root_dir


def _copy_disce_with_tests(server_root_dir: Path) -> Path:
    src_dir = Path(disce.__file__).parent.parent.parent
    disce_tests_dir = Path(__file__).parent.parent
    shutil.copytree(src_dir, server_root_dir)
    shutil.copytree(disce_tests_dir, server_root_dir / "python/disce_tests")
    shutil.rmtree(server_root_dir / "python/disce_tests/selenium")
    return server_root_dir


def _inject_tests_into_index_html(path: Path) -> None:
    path.write_text(path.read_text().replace("python/disce/__main__.py", "python/disce_tests/injected/__main__.py"))


def _inject_tests_into_pyscript_toml(python_dir: Path) -> None:
    config_toml_path = python_dir / "pyscript.toml"
    config_toml = tomlkit.parse(config_toml_path.read_text())
    packages = config_toml["packages"]
    if not isinstance(packages, tomlkit.items.Array):
        msg = "packages is not an array"
        raise TypeError(msg)
    packages.append("pytest")
    files = config_toml["files"]
    if not isinstance(files, tomlkit.items.Table):
        msg = "files is not a table"
        raise TypeError(msg)
    for entry in sorted((python_dir / "disce_tests").rglob("*")):
        if entry.is_file() and entry.suffix != ".pyc":
            relative_file = entry.relative_to(python_dir)
            files[relative_file.as_posix()] = f"./{relative_file.parent.as_posix()}/"
    config_toml_path.write_text(tomlkit.dumps(config_toml))


@pytest.fixture(scope="session")
def injected_server_url(injected_server_root_dir: Path) -> Generator[str]:
    with servers.start_server(injected_server_root_dir) as url:
        yield url


@pytest.fixture
def injected_browser(general_browser: Firefox, injected_server_url: str, capsys: pytest.CaptureFixture[str]) -> Firefox:
    browsers.prepare_browser(general_browser, injected_server_url, capsys)
    return general_browser


def test_injected(injected_browser: Firefox, capsys: pytest.CaptureFixture[str]) -> None:
    transformer_pattern = re.compile(r'^console.log: (?P<string>".*")$', flags=re.MULTILINE)
    with capsys.disabled():
        print(file=sys.stderr)  # noqa: T201
    match = outputs.watch_output(
        capsys,
        "stderr",
        timeout=timedelta(seconds=20.0),
        start_pattern=re.compile(r"running injected tests"),
        end_pattern=re.compile(r"finished injected tests, exit code: (?P<exit_code>-?[0-9]+)"),
        always_print=True,
        transformer=lambda output: transformer_pattern.sub(
            lambda match: f"| {ast.literal_eval(match['string'])}", output
        ),
    )
    exit_code = int(match["exit_code"])
    assert exit_code == 0
