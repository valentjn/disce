#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging
import re
from abc import abstractmethod
from enum import Enum, auto

import pytest
from disce.tools import ABCEnumMeta, format_plural, log_time, natural_sort_key


class TestABCEnumMeta:
    @staticmethod
    def test_new() -> None:
        class DummyEnum(Enum, metaclass=ABCEnumMeta):
            KEY = auto()

    @staticmethod
    def test_new_abstract_method() -> None:
        with pytest.raises(
            TypeError, match=r"cannot instantiate abstract class DummyAbstractEnum with abstract method some_method"
        ):

            class DummyAbstractEnum(Enum, metaclass=ABCEnumMeta):
                KEY = auto()

                @abstractmethod
                def some_method(self) -> None:
                    pass


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


def test_natural_sort_key() -> None:
    strings = ["item2", "item10", "item1", "item20", "item11", "item3"]
    assert sorted(strings, key=natural_sort_key) == ["item1", "item2", "item3", "item10", "item11", "item20"]
