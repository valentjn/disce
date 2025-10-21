#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import re
import sys
import time
from collections.abc import Callable, Generator, Sequence
from contextlib import contextmanager
from datetime import timedelta
from typing import TYPE_CHECKING, Literal

import pytest

if TYPE_CHECKING:
    from _pytest.capture import CaptureManager


def watch_output(  # noqa: PLR0913
    capsys: pytest.CaptureFixture[str],
    output_type: Literal["stdout", "stderr"],
    *,
    timeout: timedelta,
    interval: timedelta = timedelta(seconds=0.1),
    start_pattern: re.Pattern[str] | None = None,
    end_pattern: re.Pattern[str],
    return_patterns: Sequence[re.Pattern[str]] = (),
    always_print: bool = False,
    transformer: Callable[[str], str] | None = None,
) -> list[re.Match[str] | None]:
    stdout, stderr = _tee_output(capsys, transformer=transformer)
    start_time = time.monotonic()
    found_start_match = start_pattern is None
    result: list[re.Match[str] | None] = [None] * len(return_patterns)
    while time.monotonic() - start_time < timeout.total_seconds():
        output_to_search = {"stdout": stdout, "stderr": stderr}[output_type]
        if not found_start_match and start_pattern and start_pattern.search(output_to_search):
            found_start_match = True
        if found_start_match:
            for idx, pattern in enumerate(return_patterns):
                if not result[idx] and (match := pattern.search(output_to_search)):
                    result[idx] = match
            if end_pattern.search(output_to_search):
                return result
        time.sleep(interval.total_seconds())
        new_stdout, new_stderr = _tee_output(
            capsys, always_print=always_print and found_start_match, transformer=transformer
        )
        stdout += new_stdout
        stderr += new_stderr
    msg = (
        f"timeout waiting for start pattern: {start_pattern.pattern}"
        if not found_start_match and start_pattern
        else f"timeout waiting for end pattern: {end_pattern.pattern}"
    )
    raise TimeoutError(msg)


def _tee_output(
    capsys: pytest.CaptureFixture[str], *, always_print: bool = False, transformer: Callable[[str], str] | None = None
) -> tuple[str, str]:
    if not transformer:
        transformer = _identity_transformer
    stdout, stderr = capsys.readouterr()
    with capsys.disabled() if always_print else _suspend_capsys(capsys):
        print(transformer(stdout), end="")  # noqa: T201
        print(transformer(stderr), end="", file=sys.stderr)  # noqa: T201
    return stdout, stderr


def _identity_transformer(output: str) -> str:
    return output


@contextmanager
def _suspend_capsys(capsys: pytest.CaptureFixture[str]) -> Generator[None]:
    capture_manager: CaptureManager = capsys.request.config.pluginmanager.getplugin("capturemanager")
    capture_manager.suspend_fixture()
    try:
        yield
    finally:
        capture_manager.resume_fixture()
