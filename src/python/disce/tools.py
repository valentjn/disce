#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Utility functions."""

import logging
import sys
from collections.abc import Sequence
from typing import Any, override


class LoggingFormatter(logging.Formatter):
    """Custom logging formatter to adjust format based on log level."""

    @override
    def format(self, record: logging.LogRecord) -> str:
        format_ = (
            "%(name)s - %(levelname)s: %(message)s" if record.levelno >= logging.WARNING else "%(name)s: %(message)s"
        )
        self._style._fmt = format_  # noqa: SLF001
        return super().format(record)


def set_up_logging() -> None:
    """Set up logging with a custom formatter."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(LoggingFormatter())
    logging.basicConfig(level=logging.DEBUG, format="%(name)s:%(levelname)s - %(message)s", handlers=[handler])


def format_number(number_or_sequence: int | Sequence[Any], singular: str, plural: str | None = None) -> str:
    """Format a number with the correct singular/plural form of a word.

    :param number_or_sequence: Number or a sequence whose length to format.
    :param singular: Singular form of the word.
    :param plural: Plural form of the word. If ``None``, ``s`` is appended to the singular form.
    :return: Formatted string, e.g., ``"1 deck"`` or ``"3 decks"``.
    """
    number = number_or_sequence if isinstance(number_or_sequence, int) else len(number_or_sequence)
    if number == 1:
        return f"1 {singular}"
    if plural is None:
        plural = singular + "s"
    return f"{number} {plural}"
