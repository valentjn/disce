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
    source_substring: str
    """Substring from the source string."""
    source_start: int
    """Start index (inclusive) in source string."""
    source_end: int
    """End index (exclusive) in source string."""
    target_substring: str
    """Substring from the target string."""
    target_start: int
    """Start index (inclusive) in target string."""
    target_end: int
    """End index (exclusive) in target string."""

    @staticmethod
    def from_tuple(source: str, target: str, tuple_: tuple[str, int, int, int, int]) -> "Opcode":
        """Create an Opcode from a tuple."""
        tag_str, i1, i2, j1, j2 = tuple_
        return Opcode(Tag(tag_str), source[i1:i2], i1, i2, target[j1:j2], j1, j2)

    def to_html(self) -> str:
        """Render the opcode as HTML."""
        match self.tag:
            case Tag.EQUAL:
                result = f'<span class="disce-matching-answer-part">{html.escape(self.source_substring)}</span>'
            case Tag.INSERT:
                result = f"<ins>{html.escape(self.target_substring)}</ins>"
            case Tag.DELETE:
                result = f"<del>{html.escape(self.source_substring)}</del>"
            case Tag.REPLACE:
                result = (
                    f"<del>{html.escape(self.source_substring)}</del><ins>{html.escape(self.target_substring)}</ins>"
                )
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
        matcher = SequenceMatcher(a=source, b=target)
        opcodes = tuple(Opcode.from_tuple(source, target, opcode) for opcode in matcher.get_opcodes())
        return Diff(source, target, opcodes)

    def to_html(self) -> str:
        """Render the diff as HTML."""
        return "".join(opcode.to_html() for opcode in self.opcodes)
