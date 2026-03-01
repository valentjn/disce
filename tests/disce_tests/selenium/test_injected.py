# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import ast
import gzip
import logging
import re
import shutil
import sys
from base64 import b64decode
from collections.abc import Callable, Generator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from time import sleep
from typing import TYPE_CHECKING, Final

import pytest
import tomlkit
import tomlkit.items
from selenium.webdriver.support.expected_conditions import alert_is_present
from selenium.webdriver.support.ui import WebDriverWait

from disce_tests.selenium.outputs import tee_output, watch_output
from disce_tests.selenium.servers import start_server
from disce_tests.selenium.web_drivers import WebDriver, create_web_driver, prepare_web_driver

if TYPE_CHECKING:
    from selenium.webdriver.common.alert import Alert

_END_PATTERN: Final[re.Pattern[str]] = re.compile(r"finished injected tests, exit code: (?P<exit_code>-?[0-9]+)")
_CONSOLE_LOG_PATTERN: Final[re.Pattern[str]] = re.compile(r'^console.log: (?P<string>".*")$', re.MULTILINE)
_COVERAGE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r".*\.coverage file of injected tests: (?P<coverage_file>[A-Za-z0-9+/=]*).*\n?"
)

_logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def injected_server_root_dir(src_dir: Path, tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_dir = _copy_disce_with_tests(src_dir, tmp_path_factory.mktemp("server_root_dir") / "root")
    _inject_tests_into_index_html(root_dir / "index.html")
    _inject_tests_into_pyscript_toml(root_dir / "python")
    return root_dir


def _copy_disce_with_tests(src_dir: Path, server_root_dir: Path) -> Path:
    disce_tests_dir = Path(__file__).parent.parent
    shutil.copytree(src_dir, server_root_dir)
    shutil.copytree(disce_tests_dir, server_root_dir / "python/disce_tests")
    shutil.rmtree(server_root_dir / "python/disce_tests/selenium")
    return server_root_dir


def _inject_tests_into_index_html(path: Path) -> None:
    path.write_text(
        path.read_text(encoding="utf-8").replace("python/disce/__main__.py", "python/disce_tests/injected/__main__.py"),
        encoding="utf-8",
        newline="\n",
    )


def _inject_tests_into_pyscript_toml(python_dir: Path) -> None:
    config_toml_path = python_dir / "pyscript.toml"
    config_toml = tomlkit.parse(config_toml_path.read_text(encoding="utf-8"))
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
    config_toml_path.write_text(tomlkit.dumps(config_toml), encoding="utf-8", newline="\n")


@pytest.fixture(scope="module")
def server_url(injected_server_root_dir: Path) -> Generator[str]:
    with start_server(injected_server_root_dir) as url:
        yield url


@pytest.fixture(scope="module")
def download_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("download_dir")


@pytest.fixture
def web_driver(
    driver_path: Path, server_url: str, capsys: pytest.CaptureFixture[str], download_dir: Path
) -> Generator[WebDriver]:
    preferences: dict[str, str | int | bool] = {
        # don't open download dialog
        "browser.download.dir": str(download_dir),
        "browser.download.folderList": 2,
        "browser.helperApps.neverAsk.saveToDisk": "application/json",
    }
    with create_web_driver(driver_path, preferences=preferences) as web_driver:
        prepare_web_driver(web_driver, server_url, capsys)
        yield web_driver


@dataclass
class FreezeDetector:
    last_output_time: datetime | None = None
    timeout: timedelta = timedelta(seconds=10.0)
    pattern: re.Pattern[str] = re.compile(r"\[(?:ERROR|FAILED|PASSED|SKIPPED)\] *\[ *[0-9]+%\]")

    def output_transformer(self, output: str) -> str:
        now = datetime.now(tz=UTC)
        if self.pattern.search(output):
            self.last_output_time = now
        return output

    def assert_no_freeze(self) -> None:
        if self.last_output_time and datetime.now(tz=UTC) - self.last_output_time > self.timeout:
            msg = "no test output detected for too long"
            raise TimeoutError(msg)


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


def _create_signals(web_driver: WebDriver) -> Signals:
    return Signals(
        [
            Signal(
                "test_pyscript.py",
                "test_alert",
                "before_alert",
                lambda: _wait_for_alert(web_driver, "test_alert_message"),
            ),
            Signal(
                "test_pyscript.py",
                "test_confirm_accepted",
                "before_confirm",
                lambda: _wait_for_alert(web_driver, "test_confirm_accepted_message"),
            ),
            Signal(
                "test_pyscript.py",
                "test_confirm_dismissed",
                "before_confirm",
                lambda: _wait_for_alert(web_driver, "test_confirm_dismissed_message", accept=False),
            ),
            Signal(
                "test_pyscript.py",
                "test_prompt_accepted",
                "before_prompt",
                lambda: _wait_for_alert(web_driver, "test_prompt_accepted_message", input_="user_value"),
            ),
            Signal(
                "test_pyscript.py",
                "test_prompt_default",
                "before_prompt",
                lambda: _wait_for_alert(web_driver, "test_prompt_default_message"),
            ),
            Signal(
                "test_pyscript.py",
                "test_prompt_dismissed",
                "before_prompt",
                lambda: _wait_for_alert(web_driver, "test_prompt_dismissed_message", accept=False),
            ),
            Signal("test_pyscript.py", "test_upload_file", "listener_called_correctly", None),
        ]
    )


def _wait_for_alert(
    web_driver: WebDriver, expected_message: str, *, accept: bool = True, input_: str | None = None
) -> None:
    _logger.info("waiting for alert with message: %s", expected_message)
    alert: Alert = WebDriverWait(web_driver, 1.0).until(alert_is_present())
    _logger.info("alert present, reacting")
    assert alert.text == expected_message
    if input_ is not None:
        alert.send_keys(input_)
    if accept:
        alert.accept()
    else:
        alert.dismiss()


@pytest.mark.order(0)
def test_run_injected_tests(
    web_driver: WebDriver, capsys: pytest.CaptureFixture[str], request: pytest.FixtureRequest
) -> None:
    freeze_detector = FreezeDetector()
    signals = _create_signals(web_driver)
    with capsys.disabled():
        print(file=sys.stderr)  # noqa: T201
    matches = watch_output(
        capsys,
        "stderr",
        timeout=timedelta(minutes=2.0),
        start_pattern=re.compile(r"running injected tests"),
        end_pattern=_END_PATTERN,
        return_patterns=[_END_PATTERN, _COVERAGE_PATTERN],
        always_print=True,
        transformers=[
            lambda output: _COVERAGE_PATTERN.sub("", output),
            lambda output: _CONSOLE_LOG_PATTERN.sub(lambda match: f"| {ast.literal_eval(match['string'])}", output),
            freeze_detector.output_transformer,
            signals.output_transformer,
        ],
        periodic_callback=freeze_detector.assert_no_freeze,
    )
    assert matches[0] is not None
    assert int(matches[0]["exit_code"]) == 0
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
    assert (download_dir / "test_pyscript_test_download_file.json").read_text(encoding="utf-8") == '{"key": "value"}'
