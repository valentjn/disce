#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import ast
import gzip
import re
import shutil
import sys
from base64 import b64decode
from collections.abc import Callable, Generator
from dataclasses import dataclass
from datetime import timedelta
from functools import partial
from pathlib import Path
from time import sleep
from typing import TYPE_CHECKING

import disce
import pytest
import tomlkit
import tomlkit.items
from selenium.webdriver import Firefox
from selenium.webdriver.support.expected_conditions import alert_is_present
from selenium.webdriver.support.ui import WebDriverWait

from disce_tests.selenium.browsers import create_browser, prepare_browser
from disce_tests.selenium.outputs import tee_output, watch_output
from disce_tests.selenium.servers import start_server

if TYPE_CHECKING:
    from selenium.webdriver.common.alert import Alert


@pytest.fixture(scope="module")
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
    packages += ["pytest", "pytest-cov", "sqlite3"]
    files = config_toml["files"]
    if not isinstance(files, tomlkit.items.Table):
        msg = "files is not a table"
        raise TypeError(msg)
    for entry in sorted((python_dir / "disce_tests").rglob("*")):
        if entry.is_file() and entry.suffix != ".pyc":
            relative_file = entry.relative_to(python_dir)
            files[relative_file.as_posix()] = f"./{relative_file.parent.as_posix()}/"
    config_toml_path.write_text(tomlkit.dumps(config_toml))


@pytest.fixture(scope="module")
def server_url(injected_server_root_dir: Path) -> Generator[str]:
    with start_server(injected_server_root_dir) as url:
        yield url


@pytest.fixture(scope="module")
def download_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("download_dir")


@pytest.fixture
def browser(
    driver_path: Path, server_url: str, capsys: pytest.CaptureFixture[str], download_dir: Path
) -> Generator[Firefox]:
    preferences: dict[str, str | int | bool] = {
        # don't open download dialog
        "browser.download.dir": str(download_dir),
        "browser.download.folderList": 2,
        "browser.helperApps.neverAsk.saveToDisk": "application/json",
    }
    with create_browser(driver_path, preferences=preferences) as browser:
        prepare_browser(browser, server_url, capsys)
        yield browser


@dataclass
class Signal:
    filename: str
    test_name: str
    signal_name: str
    handler: Callable[[], None] | None
    received: bool = False

    @property
    def message(self) -> str:
        return f"{self.filename}::{self.test_name}: {self.signal_name}"


@dataclass
class Signals:
    signal_list: list[Signal]

    def output_transformer(self, message: str) -> str:
        for signal in self.signal_list:
            if signal.message in message:
                if signal.received:
                    msg = f"received duplicate signal: {signal.message}"
                    raise AssertionError(msg)
                if signal.handler:
                    signal.handler()
                signal.received = True
        return message

    def check_all_received(self) -> bool:
        return all(test.received for test in self.signal_list)

    def assert_all_received(self) -> None:
        missing_signals = [signal for signal in self.signal_list if not signal.received]
        if missing_signals:
            missing_messages = ", ".join(signal.message for signal in missing_signals)
            msg = f"did not receive expected signals: {missing_messages}"
            raise AssertionError(msg)


def _create_signals(browser: Firefox) -> Signals:
    return Signals(
        [
            Signal("test_pyscript.py", "test_alert", "before_alert", partial(_wait_for_alert, browser)),
            Signal("test_pyscript.py", "test_confirm_accepted", "before_confirm", partial(_wait_for_alert, browser)),
            Signal(
                "test_pyscript.py",
                "test_confirm_dismissed",
                "before_confirm",
                lambda: _wait_for_alert(browser, accept=False),
            ),
            Signal(
                "test_pyscript.py",
                "test_prompt_accepted",
                "before_prompt",
                lambda: _wait_for_alert(browser, input_="user_value"),
            ),
            Signal("test_pyscript.py", "test_prompt_default", "before_prompt", partial(_wait_for_alert, browser)),
            Signal(
                "test_pyscript.py",
                "test_prompt_dismissed",
                "before_prompt",
                lambda: _wait_for_alert(browser, accept=False),
            ),
            Signal("test_pyscript.py", "test_upload_file", "listener_called_correctly", None),
        ]
    )


def _wait_for_alert(browser: Firefox, *, accept: bool = True, input_: str | None = None) -> None:
    alert: Alert = WebDriverWait(browser, 1.0).until(alert_is_present())
    assert alert.text == "message"
    if input_ is not None:
        alert.send_keys(input_)
    if accept:
        alert.accept()
    else:
        alert.dismiss()


@pytest.mark.order(0)
def test_run_injected_tests(
    browser: Firefox, capsys: pytest.CaptureFixture[str], request: pytest.FixtureRequest
) -> None:
    signals = _create_signals(browser)
    end_pattern = re.compile(r"finished injected tests, exit code: (?P<exit_code>-?[0-9]+)")
    console_log_pattern = re.compile(r'^console.log: (?P<string>".*")$', flags=re.MULTILINE)
    coverage_pattern = re.compile(r".*\.coverage file of injected tests: (?P<coverage_file>[A-Za-z0-9+/=]*).*\n?")
    with capsys.disabled():
        print(file=sys.stderr)  # noqa: T201
    matches = watch_output(
        capsys,
        "stderr",
        timeout=timedelta(seconds=20.0),
        start_pattern=re.compile(r"running injected tests"),
        end_pattern=end_pattern,
        return_patterns=[end_pattern, coverage_pattern],
        always_print=True,
        transformers=[
            lambda output: coverage_pattern.sub("", output),
            lambda output: console_log_pattern.sub(lambda match: f"| {ast.literal_eval(match['string'])}", output),
            signals.output_transformer,
        ],
    )
    assert matches[0] is not None
    exit_code = int(matches[0]["exit_code"])
    assert exit_code == 0
    if request.config.getoption("--copy-coverage"):
        assert matches[1] is not None
        (request.config.rootpath / ".coverage").write_bytes(
            gzip.decompress(b64decode(matches[1]["coverage_file"].encode()))
        )
    if not signals.check_all_received():
        sleep(1.0)
        tee_output(capsys, transformers=[signals.output_transformer])
    signals.assert_all_received()


@pytest.mark.order(1)
def test_pyscript_download_file(download_dir: Path) -> None:
    assert (download_dir / "test_pyscript_test_download_file.json").read_text() == '{"key": "value"}'
