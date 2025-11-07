#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Tools for computing character-wise diffs between strings."""

import html
from dataclasses import dataclass
from difflib import SequenceMatcher
from enum import StrEnum, auto

from disce.furigana import TokenizedString, TokenType


class Tag(StrEnum):
    """Tag for a diff opcode."""

    DELETE = auto()
    """Deletion from source string."""
    EQUAL = auto()
    """No change between source and target string."""
    INSERT = auto()
    """Insertion into target string."""
    REPLACE = auto()
    """Replacement from source to target string."""


@dataclass(frozen=True)
class Opcode:
    """An opcode representing a diff operation between two strings."""

    tag: Tag
    """Tag indicating the type of operation."""
    source: str
    """String before applying the operation."""
    target: str
    """String after applying the operation."""

    def to_html(self) -> str:
        """Render the opcode as HTML."""
        source_html = html.escape(self.source)
        target_html = TokenizedString.from_string(self.target).html
        match self.tag:
            case Tag.EQUAL:
                result = f'<span class="disce-matching-answer-part">{target_html}</span>'
            case Tag.INSERT:
                result = f"<ins>{target_html}</ins>"
            case Tag.DELETE:
                result = f"<del>{source_html}</del>"
            case Tag.REPLACE:
                result = f"<del>{source_html}</del><ins>{target_html}</ins>"
            case _:
                msg = f"unknown tag: {self.tag}"
                raise ValueError(msg)
        return result


@dataclass(frozen=True)
class Diff:
    """A diff between two strings."""

    source: str
    """Source string."""
    target: str
    """Target string."""
    opcodes: tuple[Opcode, ...]
    """List of opcodes representing the diff."""

    @staticmethod
    def from_strings(source: str, target: str) -> "Diff":
        """Compute the diff between two strings."""
        tokenized_target = TokenizedString.from_string(target)
        stripped_target = str(tokenized_target.strip_furigana())
        matcher = SequenceMatcher(a=source, b=stripped_target)
        token_idx = 0
        token_start = 0
        opcodes = []
        for tag, source_start, source_end, target_start, target_end in matcher.get_opcodes():
            target_substring, token_idx, token_start = Diff._insert_furigana(
                stripped_target, target_start, target_end, tokenized_target, token_idx, token_start
            )
            opcodes.append(Opcode(Tag(tag), source[source_start:source_end], target_substring))
        return Diff(source, target, tuple(opcodes))

    @staticmethod
    def _insert_furigana(  # noqa: PLR0913
        target: str,
        target_start: int,
        target_end: int,
        tokenized_target: TokenizedString,
        token_idx: int,
        token_start: int,
    ) -> tuple[str, int, int]:
        """Insert furigana annotations into a target substring.

        :param target: The target string without furigana annotations.
        :param target_start: Start index (inclusive) in ``target``.
        :param target_end: End index (exclusive) in ``target``.
        :param tokenized_target: Tokenized representation of the target string.
        :param token_idx: Index of the current token in ``tokenized_target``.
        :param token_start: Start index (inclusive) of the current token in ``target``.
        :return: A tuple of the target substring with furigana annotations, the updated token index, and the
            updated token start index in ``target``.
        """
        parts = []
        last_index = target_start
        while last_index < target_end and token_idx < len(tokenized_target.tokens) and token_start < target_end:
            token = tokenized_target.tokens[token_idx]
            if token_start < last_index or token.type is not TokenType.KANJI:
                token_idx += 1
                token_start += len(token.string)
            else:
                parts.append(target[last_index:token_start])
                parts.append(str(TokenizedString(tokenized_target.tokens[token_idx : token_idx + 4])))
                last_index = token_start + len(token.string)
                token_idx += 4
                token_start += len(token.string)
        parts.append(target[last_index:target_end])
        return "".join(parts), token_idx, token_start

    def to_html(self) -> str:
        """Render the diff as HTML."""
        return "".join(opcode.to_html() for opcode in self.opcodes)
