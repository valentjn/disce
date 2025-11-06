#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pytest
from disce.furigana import FuriganaPart, FuriganaPartType


class TestFuriganaPart:
    @pytest.fixture
    def text(self) -> str:
        return 2 * "\u6f22[\u304b\u3093]\u5b57[\u3058]\u30c6\u30b9\u30c8"

    @staticmethod
    def test_parse_all(text: str) -> None:
        assert FuriganaPart.parse_all(text) == [
            FuriganaPart(FuriganaPartType.KANJI, "\u6f22", 0, 1),
            FuriganaPart(FuriganaPartType.OPENING_DELIMITER, "[", 1, 2),
            FuriganaPart(FuriganaPartType.READING, "\u304b\u3093", 2, 4),
            FuriganaPart(FuriganaPartType.CLOSING_DELIMITER, "]", 4, 5),
            FuriganaPart(FuriganaPartType.KANJI, "\u5b57", 5, 6),
            FuriganaPart(FuriganaPartType.OPENING_DELIMITER, "[", 6, 7),
            FuriganaPart(FuriganaPartType.READING, "\u3058", 7, 8),
            FuriganaPart(FuriganaPartType.CLOSING_DELIMITER, "]", 8, 9),
            FuriganaPart(FuriganaPartType.TEXT, "\u30c6\u30b9\u30c8", 9, 12),
            FuriganaPart(FuriganaPartType.KANJI, "\u6f22", 12, 13),
            FuriganaPart(FuriganaPartType.OPENING_DELIMITER, "[", 13, 14),
            FuriganaPart(FuriganaPartType.READING, "\u304b\u3093", 14, 16),
            FuriganaPart(FuriganaPartType.CLOSING_DELIMITER, "]", 16, 17),
            FuriganaPart(FuriganaPartType.KANJI, "\u5b57", 17, 18),
            FuriganaPart(FuriganaPartType.OPENING_DELIMITER, "[", 18, 19),
            FuriganaPart(FuriganaPartType.READING, "\u3058", 19, 20),
            FuriganaPart(FuriganaPartType.CLOSING_DELIMITER, "]", 20, 21),
            FuriganaPart(FuriganaPartType.TEXT, "\u30c6\u30b9\u30c8", 21, 24),
        ]

    @staticmethod
    def test_get_annotated_text(text: str) -> None:
        parts = FuriganaPart.parse_all(text)
        assert FuriganaPart.get_annotated_text(parts) == text

    @staticmethod
    def test_get_stripped_text(text: str) -> None:
        parts = FuriganaPart.parse_all(text)
        assert FuriganaPart.get_stripped_text(parts) == 2 * "\u6f22\u5b57\u30c6\u30b9\u30c8"

    @staticmethod
    def test_to_html(text: str) -> None:
        parts = FuriganaPart.parse_all(text)
        assert FuriganaPart.to_html(parts) == 2 * (
            "<ruby>\u6f22<rp>\uff08</rp><rt>\u304b\u3093</rt><rp>\uff09</rp></ruby>"
            "<ruby>\u5b57<rp>\uff08</rp><rt>\u3058</rt><rp>\uff09</rp></ruby>\u30c6\u30b9\u30c8"
        )
