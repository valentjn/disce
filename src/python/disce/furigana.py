#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Tools for parsing and handling furigana annotations in strings."""

import html
import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import ClassVar, override


class TokenType(Enum):
    """Type of a token in a furigana-annotated string."""

    KANJI = auto()
    """Kanji character for which Furigana follows."""
    OPENING_DELIMITER = auto()
    """Opening delimiter for the reading."""
    READING = auto()
    """Kana reading for the kanji character."""
    CLOSING_DELIMITER = auto()
    """Closing delimiter for the reading."""
    TEXT = auto()
    """Text other than kanji and furigana annotations."""


@dataclass(frozen=True)
class Token:
    """A token in a furigana-annotated string."""

    type: TokenType
    """Type of the token."""
    string: str
    """String of the token."""
    start: int
    """Start index (inclusive) of the token in the string."""
    end: int
    """End index (exclusive) of the token in the string."""


@dataclass(frozen=True)
class TokenizedString:
    """A tokenized string with furigana annotations."""

    tokens: tuple[Token, ...]
    """List of tokens in the string."""

    _PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"(?P<kanji>[\u4e00-\u9fff])(?P<open>\[)(?P<reading>[\u3040-\u309f]+)(?P<close>\])"
    )
    """Regex pattern to match furigana annotations."""

    @override
    def __str__(self) -> str:
        return "".join(token.string for token in self.tokens)

    @property
    def html(self) -> str:
        """HTML representation of the tokenized string with furigana."""
        parts = []
        for token in self.tokens:
            part = html.escape(token.string)
            match token.type:
                case TokenType.KANJI:
                    part = f"<ruby>{part}"
                case TokenType.OPENING_DELIMITER:
                    part = "<rp>\uff08</rp>"
                case TokenType.READING:
                    part = f"<rt>{part}</rt>"
                case TokenType.CLOSING_DELIMITER:
                    part = "<rp>\uff09</rp></ruby>"
            parts.append(part)
        return "".join(parts)

    def strip_furigana(self) -> "TokenizedString":
        """Return a new TokenizedString with furigana annotations removed."""
        return TokenizedString(tuple(token for token in self.tokens if token.type in {TokenType.KANJI, TokenType.TEXT}))

    @staticmethod
    def from_string(string: str) -> "TokenizedString":
        """Tokenize a string."""
        tokens = []
        last_index = 0
        for match in TokenizedString._PATTERN.finditer(string):
            if match.start() > last_index:
                tokens.append(Token(TokenType.TEXT, string[last_index : match.start()], last_index, match.start()))
            tokens += [
                Token(TokenType.KANJI, match["kanji"], match.start("kanji"), match.start("kanji") + 1),
                Token(TokenType.OPENING_DELIMITER, match["open"], match.start("open"), match.end("open")),
                Token(TokenType.READING, match["reading"], match.start("reading"), match.end("reading")),
                Token(TokenType.CLOSING_DELIMITER, match["close"], match.start("close"), match.end("close")),
            ]
            last_index = match.end()
        if last_index < len(string):
            tokens.append(Token(TokenType.TEXT, string[last_index:], last_index, len(string)))
        return TokenizedString(tuple(tokens))
