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
from typing import ClassVar


class FuriganaPartType(Enum):
    """Type of a part in a furigana-annotated string."""

    KANJI = auto()
    """Kanji character for which Furigana follows."""
    OPENING_DELIMITER = auto()
    """Opening delimiter for the reading."""
    READING = auto()
    """Reading (hiragana) for the kanji character."""
    CLOSING_DELIMITER = auto()
    """Closing delimiter for the reading."""
    TEXT = auto()
    """Text other than kanji and furigana annotations."""


@dataclass(frozen=True)
class FuriganaPart:
    """A part in a furigana-annotated string."""

    type: FuriganaPartType
    """Type of the part."""
    text: str
    """Text of the part."""
    start: int
    """Start index (inclusive) of the part in the string."""
    end: int
    """End index (exclusive) of the part in the string."""

    PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"(?P<kanji>[\u4e00-\u9fff])(?P<open>\[)(?P<reading>[\u3040-\u309f]+)(?P<close>\])"
    )

    @staticmethod
    def parse_all(text: str) -> "list[FuriganaPart]":
        """Parse all parts from a furigana-annotated string."""
        parts: list[FuriganaPart] = []
        last_index = 0
        for match in FuriganaPart.PATTERN.finditer(text):
            if match.start() > last_index:
                parts.append(
                    FuriganaPart(FuriganaPartType.TEXT, text[last_index : match.start()], last_index, match.start())
                )
            parts += [
                FuriganaPart(FuriganaPartType.KANJI, match["kanji"], match.start("kanji"), match.start("kanji") + 1),
                FuriganaPart(FuriganaPartType.OPENING_DELIMITER, match["open"], match.start("open"), match.end("open")),
                FuriganaPart(FuriganaPartType.READING, match["reading"], match.start("reading"), match.end("reading")),
                FuriganaPart(
                    FuriganaPartType.CLOSING_DELIMITER, match["close"], match.start("close"), match.end("close")
                ),
            ]
            last_index = match.end()
        if last_index < len(text):
            parts.append(FuriganaPart(FuriganaPartType.TEXT, text[last_index:], last_index, len(text)))
        return parts

    @staticmethod
    def get_annotated_text(parts: "list[FuriganaPart]") -> str:
        """Get the text with furigana annotations."""
        return "".join(part.text for part in parts)

    @staticmethod
    def get_stripped_text(parts: "list[FuriganaPart]") -> str:
        """Get the text with furigana annotations stripped."""
        return "".join(part.text for part in parts if part.type in {FuriganaPartType.KANJI, FuriganaPartType.TEXT})

    @staticmethod
    def to_html(parts: "list[FuriganaPart]") -> str:
        """Convert the furigana-annotated parts to HTML."""
        html_parts = []
        for part in parts:
            escaped_text = html.escape(part.text)
            match part.type:
                case FuriganaPartType.KANJI:
                    html_parts.append(f"<ruby>{escaped_text}")
                case FuriganaPartType.OPENING_DELIMITER:
                    html_parts.append("<rp>\uff08</rp>")
                case FuriganaPartType.READING:
                    html_parts.append(f"<rt>{escaped_text}</rt>")
                case FuriganaPartType.CLOSING_DELIMITER:
                    html_parts.append("<rp>\uff09</rp></ruby>")
                case _:
                    html_parts.append(escaped_text)
        return "".join(html_parts)
