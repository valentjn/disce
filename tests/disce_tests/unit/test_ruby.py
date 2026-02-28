# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pytest
from disce.ruby import Token, TokenizedString, TokenType


class TestTokenizedString:
    @staticmethod
    @pytest.fixture
    def tokenized_string(ruby_string: str) -> TokenizedString:
        return TokenizedString.from_string(ruby_string)

    @staticmethod
    def test_str(tokenized_string: TokenizedString, ruby_string: str) -> None:
        assert str(tokenized_string) == ruby_string

    @staticmethod
    def test_string_without_ruby(tokenized_string: TokenizedString, string_without_ruby: str) -> None:
        assert tokenized_string.string_without_ruby == string_without_ruby

    @staticmethod
    def test_string_without_logograms(tokenized_string: TokenizedString, string_without_logograms: str) -> None:
        assert tokenized_string.string_without_logograms == string_without_logograms

    @staticmethod
    def test_html(tokenized_string: TokenizedString, ruby_html: str) -> None:
        assert tokenized_string.html == ruby_html

    @staticmethod
    def test_from_string(tokenized_string: TokenizedString) -> None:
        assert tokenized_string == TokenizedString(
            (
                Token(TokenType.LOGOGRAM, "\u6f22", 0, 1),
                Token(TokenType.RUBY_START, "[", 1, 2),
                Token(TokenType.RUBY, "\u304b\u3093", 2, 4),
                Token(TokenType.RUBY_END, "]", 4, 5),
                Token(TokenType.LOGOGRAM, "\u5b57", 5, 6),
                Token(TokenType.RUBY_START, "[", 6, 7),
                Token(TokenType.RUBY, "\u3058", 7, 8),
                Token(TokenType.RUBY_END, "]", 8, 9),
                Token(TokenType.TEXT, "\u30c6\u30b9\u30c8", 9, 12),
                Token(TokenType.LOGOGRAM, "\u6f22", 12, 13),
                Token(TokenType.RUBY_START, "[", 13, 14),
                Token(TokenType.RUBY, "\u304b\u3093", 14, 16),
                Token(TokenType.RUBY_END, "]", 16, 17),
                Token(TokenType.LOGOGRAM, "\u5b57", 17, 18),
                Token(TokenType.RUBY_START, "[", 18, 19),
                Token(TokenType.RUBY, "\u3058", 19, 20),
                Token(TokenType.RUBY_END, "]", 20, 21),
                Token(TokenType.TEXT, "\u30c6\u30b9\u30c8", 21, 24),
            )
        )
