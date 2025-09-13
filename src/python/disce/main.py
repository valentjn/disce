#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Main module."""

import hashlib
import logging
import sys
from pathlib import Path
from typing import override

_logger = logging.getLogger(__name__)


def main() -> None:  # pragma: no cover
    """Run the main application logic."""
    from disce.screens.decks import DecksScreen  # noqa: PLC0415
    from disce.screens.load import LoadScreen  # noqa: PLC0415
    from disce.screens.tools import set_theme  # noqa: PLC0415
    from disce.storage.local import LocalStorage  # noqa: PLC0415

    set_up_logging()
    _logger.info("Disce started, source hash: %s", compute_source_hash()[:8])
    set_theme()
    DecksScreen(LocalStorage()).show()
    LoadScreen().hide()


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


def compute_source_hash() -> str:
    """Compute a hash of the source code files to detect changes."""
    hasher = hashlib.sha256()
    for file in sorted(Path(__file__).parent.rglob("*.py")):
        hasher.update(file.as_posix().encode())
        data = file.read_bytes()
        hasher.update(data)
    return hasher.hexdigest()
