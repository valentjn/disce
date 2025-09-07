#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Utility functions."""

from collections.abc import Sequence
from typing import Any


def format_plural(
    number_or_sequence: int | Sequence[Any], singular: str, plural: str | None = None, *, omit_number: bool = False
) -> str:
    """Format a number with the correct singular/plural form of a word."""
    number = number_or_sequence if isinstance(number_or_sequence, int) else len(number_or_sequence)
    if number == 1:
        suffix = singular
    elif plural is None:
        suffix = singular + "s"
    else:
        suffix = plural
    return suffix if omit_number else f"{number} {suffix}"
