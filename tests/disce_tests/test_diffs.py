#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pytest
from disce.diffs import Diff, Opcode, Tag


class TestOpcode:
    @staticmethod
    def test_from_tuple() -> None:
        assert Opcode.from_tuple("abcdef", "ghijkl", ("replace", 1, 2, 3, 4)) == Opcode(
            Tag.REPLACE, "b", 1, 2, "j", 3, 4
        )

    @staticmethod
    @pytest.mark.parametrize(
        ("opcode", "expected_html"),
        [
            (
                Opcode(Tag.EQUAL, "a&b", 0, 5, "a&b", 0, 5),
                '<span class="disce-matching-answer-part">a&amp;b</span>',
            ),
            (
                Opcode(Tag.INSERT, "", 0, 0, "a&b", 0, 3),
                "<ins>a&amp;b</ins>",
            ),
            (
                Opcode(Tag.DELETE, "a&b", 0, 3, "", 0, 0),
                "<del>a&amp;b</del>",
            ),
            (
                Opcode(Tag.REPLACE, "a&b", 0, 3, "c<d>", 0, 3),
                "<del>a&amp;b</del><ins>c&lt;d&gt;</ins>",
            ),
        ],
    )
    def test_to_html(opcode: Opcode, expected_html: str) -> None:
        assert opcode.to_html() == expected_html

    @staticmethod
    def test_to_html_unknown_tag() -> None:
        opcode = Opcode(None, "a", 0, 1, "b", 0, 1)  # type: ignore[arg-type]
        with pytest.raises(ValueError, match=r"^unknown tag: None$"):
            opcode.to_html()


class TestDiff:
    @staticmethod
    def test_from_strings() -> None:
        assert Diff.from_strings("abc", "adc") == Diff(
            "abc",
            "adc",
            (
                Opcode(Tag.EQUAL, "a", 0, 1, "a", 0, 1),
                Opcode(Tag.REPLACE, "b", 1, 2, "d", 1, 2),
                Opcode(Tag.EQUAL, "c", 2, 3, "c", 2, 3),
            ),
        )

    @staticmethod
    def test_to_html() -> None:
        diff = Diff.from_strings("a&b", "c<d>")
        assert diff.to_html() == "<del>a&amp;b</del><ins>c&lt;d&gt;</ins>"
