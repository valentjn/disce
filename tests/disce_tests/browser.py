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
import sys
import tarfile
import time
import urllib.request
import zipfile
from collections.abc import Generator
from contextlib import contextmanager, suppress
from enum import Enum, auto
from io import BufferedWriter, BytesIO, TextIOWrapper
from pathlib import Path
from threading import Event, Thread
from typing import TYPE_CHECKING

import pytest
from selenium.webdriver import Firefox, FirefoxService
from selenium.webdriver.firefox.options import Options

if TYPE_CHECKING:
    from _pytest.capture import CaptureManager

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
    options = Options()
    options.add_argument("--headless")
    options.set_preference("devtools.console.stdout.content", value=True)
    with _forward_to_stderr() as forwarded_stderr:
        service = FirefoxService(executable_path=str(driver_path), log_output=forwarded_stderr)
        browser = Firefox(options=options, service=service)
        yield browser
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
def browser(
    general_browser: Firefox, server_url: str, request: pytest.FixtureRequest, capsys: pytest.CaptureFixture[str]
) -> Firefox:
    url = f"{server_url.rstrip('/')}/{getattr(request, 'param', '').lstrip('/')}"
    browser = general_browser
    browser.get(url)
    stdout, stderr = _tee_output(capsys)
    start_time = time.monotonic()
    while "Disce started" not in stderr and time.monotonic() - start_time < 20.0:
        time.sleep(0.5)
        new_stdout, new_stderr = _tee_output(capsys)
        stdout += new_stdout
        stderr += new_stderr
    if "Disce started" in stderr:
        time.sleep(0.5)
    else:
        _logger.warning("timeout waiting for Disce to start")
    return browser


def _tee_output(capsys: pytest.CaptureFixture[str]) -> tuple[str, str]:
    capture_manager: CaptureManager = capsys.request.config.pluginmanager.getplugin("capturemanager")
    stdout, stderr = capsys.readouterr()
    capture_manager.suspend_fixture()
    try:
        print(stdout, end="")  # noqa: T201
        print(stderr, end="", file=sys.stderr)  # noqa: T201
    finally:
        capture_manager.resume_fixture()
    return stdout, stderr
