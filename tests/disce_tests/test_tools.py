#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging
import re

import pytest
from disce.tools import format_plural, log_time


@pytest.mark.parametrize(
    ("number_or_sequence", "singular", "plural", "omit_number", "expected"),
    [
        (1, "apple", None, False, "1 apple"),
        (2, "apple", None, False, "2 apples"),
        (0, "apple", None, False, "0 apples"),
        ([1], "item", None, False, "1 item"),
        ([1, 2], "item", None, False, "2 items"),
        (1, "child", "children", False, "1 child"),
        (3, "child", "children", False, "3 children"),
        (1, "goose", "geese", True, "goose"),
        (2, "goose", "geese", True, "geese"),
        ([1, 2, 3], "cat", None, True, "cats"),
        ([], "dog", None, False, "0 dogs"),
    ],
)
def test_format_plural(
    number_or_sequence: int | list[int], singular: str, plural: str, *, omit_number: bool, expected: str
) -> None:
    assert format_plural(number_or_sequence, singular, plural, omit_number=omit_number) == expected


def test_log_time(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    msg = "Test block"
    with log_time(msg):
        pass
    pattern = re.compile(rf"{re.escape(msg)} in \d+\.\d{{2}} ms")
    assert any(record.levelno == logging.DEBUG and pattern.match(record.getMessage()) for record in caplog.records)
