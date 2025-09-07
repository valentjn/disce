#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Main module."""

import logging
import sys
from typing import override

# import all screens to register event handlers
from disce.screens import *  # noqa: F403  # isort: skip

from disce.screens import load as load_screen
from disce.screens import main as main_screen

_logger = logging.getLogger(__name__)


class LoggingFormatter(logging.Formatter):
    """Custom logging formatter to adjust format based on log level."""

    @override
    def format(self, record: logging.LogRecord) -> str:
        format_ = (
            "%(name)s - %(levelname)s: %(message)s" if record.levelno >= logging.WARNING else "%(name)s: %(message)s"
        )
        self._style._fmt = format_  # noqa: SLF001
        return super().format(record)


def main() -> None:
    """Run the main application logic."""
    set_up_logging()
    _logger.info("application started")
    main_screen.show()
    load_screen.hide()


def set_up_logging() -> None:
    """Set up logging with a custom formatter."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(LoggingFormatter())
    logging.basicConfig(level=logging.DEBUG, format="%(name)s:%(levelname)s - %(message)s", handlers=[handler])
