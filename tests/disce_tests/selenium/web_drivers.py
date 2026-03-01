# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import logging
import platform
import re
import sys
import tarfile
import time
import urllib.request
import zipfile
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from datetime import timedelta
from enum import Enum, auto
from io import BytesIO
from pathlib import Path
from threading import Thread
from typing import TextIO

import pytest
from pydantic import BaseModel
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.webdriver import WebDriver as _WebDriver

from disce_tests.selenium.outputs import watch_output

WebDriver = _WebDriver

_logger = logging.getLogger(__name__)


class _OperatingSystem(Enum):
    LINUX = auto()
    MACOS = auto()
    WINDOWS = auto()

    @staticmethod
    def current() -> "_OperatingSystem":
        return {
            "linux": _OperatingSystem.LINUX,
            "darwin": _OperatingSystem.MACOS,
            "win32": _OperatingSystem.WINDOWS,
        }[sys.platform]


class _Architecture(Enum):
    AARCH64 = auto()
    X86 = auto()
    X86_64 = auto()

    @staticmethod
    def current() -> "_Architecture":
        machine = platform.machine()
        if machine in {"aarch64", "arm64"}:
            return _Architecture.AARCH64
        if "64" in machine:
            return _Architecture.X86_64
        return _Architecture.X86


class _GitHubReleaseAsset(BaseModel):
    browser_download_url: str


class _GitHubRelease(BaseModel):
    tag_name: str
    assets: list[_GitHubReleaseAsset]


@pytest.fixture(scope="session")
def web_driver_path(pytestconfig: pytest.Config) -> Path:
    operating_system, architecture = _OperatingSystem.current(), _Architecture.current()
    web_driver_dir = pytestconfig.cache.mkdir("geckodriver")
    web_driver_filename = "geckodriver.exe" if operating_system is _OperatingSystem.WINDOWS else "geckodriver"
    web_driver_path = web_driver_dir / web_driver_filename
    if web_driver_path.exists():
        _logger.info("using cached geckodriver from %s", web_driver_path)
        return web_driver_path
    with urllib.request.urlopen("https://api.github.com/repos/mozilla/geckodriver/releases/latest") as response:
        release = _GitHubRelease.model_validate_json(response.read())
    suffix = {
        (_OperatingSystem.LINUX, _Architecture.AARCH64): "linux-aarch64.tar.gz",
        (_OperatingSystem.LINUX, _Architecture.X86_64): "linux64.tar.gz",
        (_OperatingSystem.LINUX, _Architecture.X86): "linux32.tar.gz",
        (_OperatingSystem.MACOS, _Architecture.AARCH64): "macos-aarch64.tar.gz",
        (_OperatingSystem.MACOS, _Architecture.X86_64): "macos.tar.gz",
        (_OperatingSystem.WINDOWS, _Architecture.AARCH64): "win-aarch64.zip",
        (_OperatingSystem.WINDOWS, _Architecture.X86_64): "win64.zip",
        (_OperatingSystem.WINDOWS, _Architecture.X86): "win32.zip",
    }[(operating_system, architecture)]
    asset_url = next(
        asset.browser_download_url for asset in release.assets if asset.browser_download_url.endswith(suffix)
    )
    _logger.info("downloading geckodriver from %s", asset_url)
    with urllib.request.urlopen(asset_url) as response:
        archive = response.read()
    with BytesIO(archive) as archive_file:
        if suffix.endswith(".zip"):
            with zipfile.ZipFile(archive_file) as zip_file:
                zip_file.extract(web_driver_filename, path=web_driver_dir)
        else:
            with tarfile.open(fileobj=archive_file) as tar_file:
                tar_file.extract("geckodriver", filter="data", path=web_driver_dir)
    return web_driver_path


@contextmanager
def create_web_driver(
    web_driver_path: Path, log_file_path: Path, preferences: Mapping[str, str | int | bool] | None = None
) -> Generator[WebDriver]:
    options = Options()
    options.add_argument("--headless")
    default_preferences: dict[str, str | int | bool] = {
        # enable logging from the browser console
        "devtools.console.stdout.content": True,
        # disable beforeunload dialogs
        "dom.disable_beforeunload": True,
    }
    preferences = default_preferences | (dict(preferences) if preferences else {})
    for key, value in preferences.items():
        options.set_preference(key, value)
    service = Service(executable_path=str(web_driver_path), log_output=str(log_file_path))
    web_driver = WebDriver(options=options, service=service)
    try:
        yield web_driver
    finally:
        thread = Thread(target=web_driver.quit, daemon=True)
        thread.start()
        thread.join(timeout=5.0)
        if thread.is_alive():
            _logger.warning("timed out waiting for browser to quit, killing the process")
            web_driver.service.process.kill()


def prepare_web_driver(
    web_driver: WebDriver, server_url: str, log_file: TextIO, capsys: pytest.CaptureFixture[str]
) -> WebDriver:
    web_driver.get(server_url)
    watch_output(log_file, capsys, timeout=timedelta(seconds=20.0), end_pattern=re.compile(r"Disce started"))
    time.sleep(0.5)
    return web_driver
