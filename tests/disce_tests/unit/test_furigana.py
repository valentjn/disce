#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from disce.furigana import Token, TokenizedString, TokenType


class TestTokenizedString:
    @staticmethod
    def test_str(furigana_string: str) -> None:
        assert str(TokenizedString.from_string(furigana_string)) == furigana_string

    @staticmethod
    def test_html(furigana_string: str, furigana_html: str) -> None:
        tokenized = TokenizedString.from_string(furigana_string)
        assert tokenized.html == furigana_html

    @staticmethod
    def test_strip_furigana(furigana_string: str, furigana_stripped: str) -> None:
        stripped = TokenizedString.from_string(furigana_string).strip_furigana()
        assert stripped == TokenizedString(
            (
                Token(TokenType.KANJI, "\u6f22", 0, 1),
                Token(TokenType.KANJI, "\u5b57", 5, 6),
                Token(TokenType.TEXT, "\u30c6\u30b9\u30c8", 9, 12),
                Token(TokenType.KANJI, "\u6f22", 12, 13),
                Token(TokenType.KANJI, "\u5b57", 17, 18),
                Token(TokenType.TEXT, "\u30c6\u30b9\u30c8", 21, 24),
            )
        )
        assert str(stripped) == furigana_stripped

    @staticmethod
    def test_from_string(furigana_string: str) -> None:
        assert TokenizedString.from_string(furigana_string) == TokenizedString(
            (
                Token(TokenType.KANJI, "\u6f22", 0, 1),
                Token(TokenType.OPENING_DELIMITER, "[", 1, 2),
                Token(TokenType.READING, "\u304b\u3093", 2, 4),
                Token(TokenType.CLOSING_DELIMITER, "]", 4, 5),
                Token(TokenType.KANJI, "\u5b57", 5, 6),
                Token(TokenType.OPENING_DELIMITER, "[", 6, 7),
                Token(TokenType.READING, "\u3058", 7, 8),
                Token(TokenType.CLOSING_DELIMITER, "]", 8, 9),
                Token(TokenType.TEXT, "\u30c6\u30b9\u30c8", 9, 12),
                Token(TokenType.KANJI, "\u6f22", 12, 13),
                Token(TokenType.OPENING_DELIMITER, "[", 13, 14),
                Token(TokenType.READING, "\u304b\u3093", 14, 16),
                Token(TokenType.CLOSING_DELIMITER, "]", 16, 17),
                Token(TokenType.KANJI, "\u5b57", 17, 18),
                Token(TokenType.OPENING_DELIMITER, "[", 18, 19),
                Token(TokenType.READING, "\u3058", 19, 20),
                Token(TokenType.CLOSING_DELIMITER, "]", 20, 21),
                Token(TokenType.TEXT, "\u30c6\u30b9\u30c8", 21, 24),
            )
        )
