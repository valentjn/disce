#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pytest
from disce.diffs import Diff, Opcode, Tag


class TestOpcode:
    EXPECTED_RUBY_HTML = "<ruby>\u6f22<rp>\uff08</rp><rt>\u304b\u3093</rt><rp>\uff09</rp></ruby>"

    @staticmethod
    @pytest.mark.parametrize(
        ("opcode", "expected_html"),
        [
            (Opcode(Tag.EQUAL, "a&b", "a&b"), '<span class="disce-matching-answer-part">a&amp;b</span>'),
            (Opcode(Tag.INSERT, "", "a&b"), "<ins>a&amp;b</ins>"),
            (Opcode(Tag.DELETE, "a&b", ""), "<del>a&amp;b</del>"),
            (Opcode(Tag.REPLACE, "a&b", "c<d>"), "<del>a&amp;b</del><ins>c&lt;d&gt;</ins>"),
            (
                Opcode(Tag.EQUAL, "\u6f22", "\u6f22[\u304b\u3093]"),
                f'<span class="disce-matching-answer-part">{EXPECTED_RUBY_HTML}</span>',
            ),
            (Opcode(Tag.INSERT, "", "\u6f22[\u304b\u3093]"), f"<ins>{EXPECTED_RUBY_HTML}</ins>"),
            (
                Opcode(Tag.REPLACE, "\u6f22", "\u6f22[\u304b\u3093]"),
                f"<del>\u6f22</del><ins>{EXPECTED_RUBY_HTML}</ins>",
            ),
        ],
    )
    def test_to_html(opcode: Opcode, expected_html: str) -> None:
        assert opcode.to_html() == expected_html

    @staticmethod
    def test_to_html_unknown_tag() -> None:
        opcode = Opcode(None, "a", "b")  # type: ignore[arg-type]
        with pytest.raises(ValueError, match=r"^unknown tag: None$"):
            opcode.to_html()


class TestDiff:
    @staticmethod
    def test_from_strings() -> None:
        assert Diff.from_strings("abc", "adc") == Diff(
            "abc", "adc", (Opcode(Tag.EQUAL, "a", "a"), Opcode(Tag.REPLACE, "b", "d"), Opcode(Tag.EQUAL, "c", "c"))
        )

    @staticmethod
    def test_from_strings_furigana() -> None:
        source = 2 * "\u6f22\u5b57\u30c6\u30b9\u30c8"
        target = 2 * "\u6f22[\u304b\u3093]\u30c6\u30b9\u30c8\u5b57[\u3058]"
        assert Diff.from_strings(source, target) == Diff(
            source,
            target,
            2
            * (
                Opcode(Tag.EQUAL, "\u6f22", "\u6f22[\u304b\u3093]"),
                Opcode(Tag.DELETE, "\u5b57", ""),
                Opcode(Tag.EQUAL, "\u30c6\u30b9\u30c8", "\u30c6\u30b9\u30c8"),
                Opcode(Tag.INSERT, "", "\u5b57[\u3058]"),
            ),
        )

    @staticmethod
    def test_to_html() -> None:
        diff = Diff.from_strings("a&b", "c<d>")
        assert diff.to_html() == "<del>a&amp;b</del><ins>c&lt;d&gt;</ins>"
