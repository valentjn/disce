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

from disce.furigana import FuriganaPart, FuriganaPartType


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
        target_html = FuriganaPart.to_html(FuriganaPart.parse_all(self.target))
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
        furigana_parts = FuriganaPart.parse_all(target)
        stripped_target = FuriganaPart.get_stripped_text(furigana_parts)
        matcher = SequenceMatcher(a=source, b=stripped_target)
        furigana_index = 0
        furigana_start = 0
        opcodes = []
        for tag, source_start, source_end, target_start, target_end in matcher.get_opcodes():
            target_substring, furigana_index, furigana_start = Diff._insert_furigana(
                stripped_target, target_start, target_end, furigana_parts, furigana_index, furigana_start
            )
            opcodes.append(Opcode(Tag(tag), source[source_start:source_end], target_substring))
        return Diff(source, target, tuple(opcodes))

    @staticmethod
    def _insert_furigana(  # noqa: PLR0913
        target: str,
        target_start: int,
        target_end: int,
        furigana_parts: list[FuriganaPart],
        furigana_part_idx: int,
        furigana_part_start: int,
    ) -> tuple[str, int, int]:
        """Insert furigana annotations into a target substring.

        :param target: The target string without furigana annotations.
        :param target_start: Start index (inclusive) in ``target``.
        :param target_end: End index (exclusive) in ``target``.
        :param furigana_parts: List of furigana parts to insert.
        :param furigana_part_idx: Index of the current furigana part.
        :param furigana_part_start: Start index (inclusive) of the current furigana part in ``target``.
        :return: A tuple of the target substring with furigana annotations, the updated furigana part index, and the
            updated furigana part start index in ``target``.
        """
        parts = []
        last_index = target_start
        while last_index < target_end and furigana_part_idx < len(furigana_parts) and furigana_part_start < target_end:
            part = furigana_parts[furigana_part_idx]
            if furigana_part_start < last_index or part.type is not FuriganaPartType.KANJI:
                furigana_part_idx += 1
                furigana_part_start += len(part.text)
            else:
                parts.append(target[last_index:furigana_part_start])
                parts.append(FuriganaPart.get_annotated_text(furigana_parts[furigana_part_idx : furigana_part_idx + 4]))
                last_index = furigana_part_start + len(part.text)
                furigana_part_idx += 4
                furigana_part_start += len(part.text)
        parts.append(target[last_index:target_end])
        return "".join(parts), furigana_part_idx, furigana_part_start

    def to_html(self) -> str:
        """Render the diff as HTML."""
        return "".join(opcode.to_html() for opcode in self.opcodes)
