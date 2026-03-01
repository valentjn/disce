# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import re
import sys
import time
from collections.abc import Callable, Sequence
from contextlib import nullcontext
from datetime import timedelta
from typing import TextIO

import pytest


def watch_output(  # noqa: PLR0913
    file: TextIO,
    capsys: pytest.CaptureFixture[str],
    *,
    timeout: timedelta,
    interval: timedelta = timedelta(milliseconds=100.0),
    start_pattern: re.Pattern[str] | None = None,
    end_pattern: re.Pattern[str],
    return_patterns: Sequence[re.Pattern[str]] = (),
    always_print: bool = False,
    transformers: Sequence[Callable[[str], str]] = (),
    periodic_callback: Callable[[], None] | None = None,
) -> list[re.Match[str] | None]:
    output = tee_output(file, capsys, transformers=transformers)
    start_time = time.monotonic()
    found_start_match = start_pattern is None
    result: list[re.Match[str] | None] = [None] * len(return_patterns)
    while time.monotonic() - start_time < timeout.total_seconds():
        if periodic_callback:
            periodic_callback()
        if not found_start_match and start_pattern and start_pattern.search(output):
            found_start_match = True
        if found_start_match:
            for idx, pattern in enumerate(return_patterns):
                if not result[idx] and (match := pattern.search(output)):
                    result[idx] = match
            if end_pattern.search(output):
                return result
        time.sleep(interval.total_seconds())
        output += tee_output(file, capsys, always_print=always_print and found_start_match, transformers=transformers)
    msg = (
        f"timeout waiting for start pattern: {start_pattern.pattern}"
        if not found_start_match and start_pattern
        else f"timeout waiting for end pattern: {end_pattern.pattern}"
    )
    raise TimeoutError(msg)


def tee_output(
    file: TextIO,
    capsys: pytest.CaptureFixture[str],
    *,
    all_output: bool = False,
    always_print: bool = False,
    transformers: Sequence[Callable[[str], str]] = (),
) -> str:
    if all_output:
        file.seek(0)
        output = file.read()
    else:
        output = "".join(file.readlines())
    if output:
        transformed_output = output
        for transformer in transformers:
            transformed_output = transformer(transformed_output)
        if transformed_output:
            with capsys.disabled() if always_print else nullcontext():
                print(transformed_output, end="", file=sys.stderr)  # noqa: T201
    return output
