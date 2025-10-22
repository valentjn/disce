#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import json
import logging
import os
import platform
import re
import sys
import tarfile
import time
import urllib.request
import zipfile
from collections.abc import Generator, Mapping
from contextlib import contextmanager, suppress
from datetime import timedelta
from enum import Enum, auto
from io import BufferedWriter, BytesIO, TextIOWrapper
from pathlib import Path
from threading import Event, Thread

import pytest
from selenium.webdriver import Firefox, FirefoxService
from selenium.webdriver.firefox.options import Options

from disce_tests.selenium.outputs import watch_output

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


@pytest.fixture(scope="session")
def driver_path(pytestconfig: pytest.Config) -> Path:
    operating_system, architecture = _OperatingSystem.current(), _Architecture.current()
    geckodriver_dir = pytestconfig.cache.mkdir("geckodriver")
    geckodriver_filename = "geckodriver.exe" if operating_system is _OperatingSystem.WINDOWS else "geckodriver"
    geckodriver_path = geckodriver_dir / geckodriver_filename
    if geckodriver_path.exists():
        _logger.info("Using cached geckodriver from %s", geckodriver_path)
        return geckodriver_path
    with urllib.request.urlopen("https://api.github.com/repos/mozilla/geckodriver/releases/latest") as response:
        release_info = json.load(response)
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
        asset["browser_download_url"]
        for asset in release_info["assets"]
        if asset["browser_download_url"].endswith(suffix)
    )
    _logger.info("Downloading geckodriver from %s", asset_url)
    with urllib.request.urlopen(asset_url) as response:
        archive = response.read()
    with BytesIO(archive) as archive_file:
        if suffix.endswith(".zip"):
            with zipfile.ZipFile(archive_file) as zip_file:
                zip_file.extract(geckodriver_filename, path=geckodriver_dir)
        else:
            with tarfile.open(fileobj=archive_file) as tar_file:
                tar_file.extract("geckodriver", filter="data", path=geckodriver_dir)
    return geckodriver_path


@pytest.fixture(scope="session")
def general_browser(driver_path: Path) -> Generator[Firefox]:
    with create_browser(driver_path) as browser:
        yield browser


@contextmanager
def create_browser(driver_path: Path, preferences: Mapping[str, str | int | bool] | None = None) -> Generator[Firefox]:
    options = Options()
    options.add_argument("--headless")
    options.set_preference("devtools.console.stdout.content", value=True)
    preferences = preferences or {}
    for key, value in preferences.items():
        options.set_preference(key, value)
    with _forward_to_stderr() as forwarded_stderr:
        service = FirefoxService(executable_path=str(driver_path), log_output=forwarded_stderr)
        browser = Firefox(options=options, service=service)
        try:
            yield browser
        finally:
            browser.quit()


@contextmanager
def _forward_to_stderr() -> Generator[BufferedWriter]:
    def forward_loop() -> None:
        reader_wrapper = TextIOWrapper(reader)
        try:
            while not exit_thread_event.is_set():
                chunk = reader_wrapper.readline()
                if chunk:
                    print(chunk, end="", file=sys.stderr)  # noqa: T201
                else:
                    time.sleep(0.1)
        finally:
            with suppress(Exception):
                reader_wrapper.close()

    read_fd, write_fd = os.pipe()
    os.set_blocking(read_fd, False)
    os.set_inheritable(write_fd, True)  # noqa: FBT003
    with os.fdopen(read_fd, "rb") as reader, os.fdopen(write_fd, "wb") as writer:
        exit_thread_event = Event()
        thread = Thread(target=forward_loop, daemon=True)
        thread.start()
        try:
            yield writer
        finally:
            exit_thread_event.set()
            thread.join(timeout=1.0)


@pytest.fixture
def browser(general_browser: Firefox, server_url: str, capsys: pytest.CaptureFixture[str]) -> Firefox:
    prepare_browser(general_browser, server_url, capsys)
    return general_browser


def prepare_browser(browser: Firefox, server_url: str, capsys: pytest.CaptureFixture[str]) -> Firefox:
    browser.get(server_url)
    watch_output(capsys, "stderr", timeout=timedelta(seconds=20.0), end_pattern=re.compile(r"Disce started"))
    time.sleep(0.5)
    return browser
