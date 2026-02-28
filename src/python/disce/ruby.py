# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Tools for parsing and handling ruby annotations in strings."""

import html
import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import ClassVar, override


class TokenType(Enum):
    """Type of a token in a ruby-annotated string."""

    LOGOGRAM = auto()
    """Logogram (e.g., Kanji character) for which ruby follows."""
    RUBY_START = auto()
    """Delimiter indicating the start of ruby annotation."""
    RUBY = auto()
    """Ruby characters for the logogram."""
    RUBY_END = auto()
    """Delimiter indicating the end of ruby annotation."""
    TEXT = auto()
    """Text other than logograms and ruby annotations."""


@dataclass(frozen=True)
class Token:
    """A token in a ruby-annotated string."""

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
    """A tokenized string with ruby annotations."""

    tokens: tuple[Token, ...]
    """List of tokens in the string."""

    _PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"(?P<logogram>[\u4e00-\u9fff])(?P<ruby_start>\[)(?P<ruby>[\u3040-\u309f]+)(?P<ruby_end>\])"
    )
    """Regex pattern to match ruby annotations."""

    @override
    def __str__(self) -> str:
        """Original ruby-annotated string."""
        return "".join(token.string for token in self.tokens)

    @property
    def string_without_ruby(self) -> str:
        """String without ruby annotations."""
        return "".join(token.string for token in self.tokens if token.type in {TokenType.LOGOGRAM, TokenType.TEXT})

    @property
    def html(self) -> str:
        """HTML representation of the tokenized string with ruby annotations."""
        parts = []
        for token in self.tokens:
            part = html.escape(token.string)
            match token.type:
                case TokenType.LOGOGRAM:
                    part = f"<ruby>{part}"
                case TokenType.RUBY_START:
                    part = "<rp>\uff08</rp>"
                case TokenType.RUBY:
                    part = f"<rt>{part}</rt>"
                case TokenType.RUBY_END:
                    part = "<rp>\uff09</rp></ruby>"
            parts.append(part)
        return "".join(parts)

    @staticmethod
    def from_string(string: str) -> "TokenizedString":
        """Tokenize a string."""
        tokens = []
        last_index = 0
        for match in TokenizedString._PATTERN.finditer(string):
            if match.start() > last_index:
                tokens.append(Token(TokenType.TEXT, string[last_index : match.start()], last_index, match.start()))
            tokens += [
                Token(TokenType.LOGOGRAM, match["logogram"], match.start("logogram"), match.start("logogram") + 1),
                Token(TokenType.RUBY_START, match["ruby_start"], match.start("ruby_start"), match.end("ruby_start")),
                Token(TokenType.RUBY, match["ruby"], match.start("ruby"), match.end("ruby")),
                Token(TokenType.RUBY_END, match["ruby_end"], match.start("ruby_end"), match.end("ruby_end")),
            ]
            last_index = match.end()
        if last_index < len(string):
            tokens.append(Token(TokenType.TEXT, string[last_index:], last_index, len(string)))
        return TokenizedString(tuple(tokens))
